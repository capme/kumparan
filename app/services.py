import os
import re
import csv
import tempfile
import pytz
import time
import datetime as dt
from typing import NamedTuple
import pysftp
from django.conf import settings
from paramiko.ssh_exception import SSHException
from common.utils import generate_csv, GenerateXLS
from mapemall.cpms import CPMS, CPMSInvalidAuthError
from mapemall.models import Orders, OrderItems, Brand
from datetime import datetime
from config.log import logger
from django.db import transaction, DatabaseError


def get_configs():
    config = settings.MAPEMALL_FTPS
    yield ('lfc', config['map_lfc'],)
    yield ('map', config['map_map'],)
    yield ('brooks', config['map_brooks'],)


class MapSalesOrderFile(NamedTuple):
    name: str
    remote: str
    local: str
    sftp: pysftp.Connection = None

    def archive(self, archive_dir='Archive'):
        self.sftp.rename(self.remote, os.path.join(os.path.dirname(self.remote), "{}/{}".format(archive_dir, self.name)))

    # Parsing format from csv to JSON
    def get_order(self) -> list:
        order_data = []
        with open(self.local, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                order_data.append(row)
        return order_data

    # Mapping format to CPMS
    def get_order_id_column(self, channel):
        order_id = ''
        if channel == 'map':
            order_id = 'Magento Order #'
        elif channel == 'lfc':
            order_id = 'Order #'
        elif channel == 'brooks':
            order_id = 'Order #'
        return order_id

    @staticmethod
    def validate(datetime_string):
        try:
            dt.datetime.strptime(datetime_string, str("%d/%m/%Y %H:%M"))
            return True
        except ValueError:
            return False

    def format_datetime(self, date):
        if self.validate(date) is False:
            parse = dt.datetime.strptime(date, str("%d/%m/%Y")).isoformat() + str('Z')
        else:
            parse = dt.datetime.strptime(date, str("%d/%m/%Y %H:%M")).isoformat() + str('Z')
        return parse

    @staticmethod
    def shipping_type(shipping):
        if (shipping == "Standard 2-4 Days") or (shipping == "Free Shipping"):
            shipping = "STANDARD_2_4_DAYS"
        return shipping

    @staticmethod
    def payment_type(payment):
        if payment == "Cash On Delivery":
            payment = "COD"
        elif payment == "No Payment Information Required":
            payment = "NO_PAYMENT"
        else:
            payment = "NON_COD"
        return payment

    def mapping_cpms(self, channel, order_data):
        list_cpms_format = dict()
        order_id_column = self.get_order_id_column(channel)

        for row in order_data:
            order_id = str(row[order_id_column])
            if order_id not in list_cpms_format:
                # new
                date = row['Order Date']
                list_cpms_format[order_id] = {
                    "orderCreatedTime": self.format_datetime(date),
                    "orderId": order_id,
                    "paymentType": self.payment_type(row['Payment Type']),
                    "shippingType": self.shipping_type(row['Shipping Type']),
                    "grossTotal": int(float(row['Gross Total'])),
                    "currUnit": "IDR",
                    "customerInfo": {
                        "addressee": row['Shipping Adressee'],
                        "address1": row['Shipping Address Line 1'],
                        "postalCode": str(row['Shipping Address Postal Code']),
                        "country": row['Shipping Address Country'],
                        "phone": str(row['Shipping Address Phone'])
                    },
                    "orderShipmentInfo": {
                        "addressee": row['Shipping Adressee'],
                        "address1": row['Shipping Address Line 1'],
                        "address2": row['Shipping Address Line 2'],
                        "subDistrict": "",
                        "district": "",
                        "city": row['Shipping Address City'],
                        "province": row['Shipping Address State/Province'],
                        "postalCode": str(row['Shipping Address Postal Code']),
                        "country": row['Shipping Address Country'],
                        "phone": str(row['Shipping Address Phone']),
                        "email": row['Email']
                    },
                    "orderItems": [],
                    "status": "NEW"
                }

            # existing
            list_cpms_format[order_id]['orderItems'].append({
                "partnerId": str(settings.PARTNER_ID),
                "itemId": row['Item ID'],
                "qty": int(row['QTY']),
                "subTotal": int(float(row['Gross Total']))
            })

        return list_cpms_format


class SFTPService:
    def __init__(self, sftp_params: dict):
        self.sftp = None
        self.sftp_params = {key: sftp_params.get(key) for key in ['host',
                                                                  'username',
                                                                  'private_key',
                                                                  'password',
                                                                  'port',
                                                                  'private_key_pass',
                                                                  'ciphers',
                                                                  'log',
                                                                  'cnopts',
                                                                  'default_path']}

    def __enter__(self):
        while True:
            try:
                self.sftp = pysftp.Connection(**self.sftp_params)
            except SSHException as e:
                if 'Error reading SSH protocol banner' in e.args[0]:
                    time.sleep(1)
                    continue
                raise
            else:
                break
        self.tmp_dir = tempfile.TemporaryDirectory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tmp_dir.cleanup()
        self.sftp.close()

    def get_files(self, dir):
        files = self.sftp.listdir(dir)
        for file_name in files:
            if not self.sftp.isfile("{}/{}".format(dir, file_name)):
                continue
            if not self.get_files_validator(file_name):
                continue
            remote = os.path.join(dir, file_name)
            local = os.path.join(self.tmp_dir.name, file_name)
            self.sftp.get(remote, local)
            yield self.get_files_format_item(file_name, local, remote)

    def get_files_validator(self, file_name):
        return True

    def get_files_format_item(self, file_name, local, remote):
        return local

    def put(self, src, dest):
        print(self.sftp)
        self.sftp.put(src, dest)


class MapSalesOrderFilesService(SFTPService):
    """Iterator to connect to SFTP, retrieve files, and move it to archive"""
    def get_files_validator(self, file_name):
        return re.search(r'\.csv', file_name, re.IGNORECASE) is not None

    def get_files_format_item(self, file_name, local, remote):
        return MapSalesOrderFile(name=file_name, local=local, remote=remote, sftp=self.sftp)


class AgilitySalesOrderFilesService(SFTPService):

    def __init__(self):
        now = datetime.now()
        self.list_obj_db = []
        self.orders = Orders.objects.filter()
        timezone = pytz.timezone(settings.TIMEZONE)
        local_time = timezone.localize(now)
        date_time = datetime.strftime(local_time, str('%d%m%Y_%H%M%S'))
        self.agility_file_name = 'CM_MAP_AGI_SALE_ORDER_{}'.format(date_time)

    def generate_order_id(self, channel, content):
        order_id = ''
        if channel == 'map':
            order_id = 'MEM_{}'.format(content.magento_order)
        elif channel == 'lfc':
            order_id = 'LFC_{}'.format(content.magento_order)
        elif channel == 'brooks':
            order_id = 'BRO_{}'.format(content.magento_order)
        return order_id

    def get_udf2(self, channel):
        source = ''
        if channel == 'map':
            source = 'EM88'
        elif channel == 'lfc':
            source = 'E105'
        elif channel == 'brooks':
            source = 'E108'
        return source

    def notes(self, channel):
        source = ''
        if channel == 'map':
            source = 'MAPEmall'
        elif channel == 'lfc':
            source = 'Liverpool FC'
        elif channel == 'brooks':
            source = 'brooks'
        return source

    def generate_order_date(self, content):
        try:
            content_order_date = datetime.strptime(content.order_date, str('%d/%m/%Y %H:%M'))
        except:
            content_order_date = datetime.strptime(content.order_date, str('%d/%m/%Y'))

        order_date = content_order_date.strftime(str('%d/%m/%Y'))
        return order_date

    def payment_type(self, payment):
        if payment == "Cash On Delivery":
            payment = "COD"
        else:
            payment = "NonCOD"
        return payment

    def get_data_for_agility(self):
        """Get Data For Generate Agility"""
        data = Orders.objects.filter(agility_generated=False)
        list_data = []
        header = ['WhseID', 'STOREKEY', 'ExternalOrder', 'OrderGroup', 'OrderDate', 'DeliveryDate', 'CONSIGNEEKey',
                  'ConsigneeCONTACT1', 'ConsigneeCONTACT2', 'ConsigneeCOMPANY', 'ConsigneeAddress1',
                  'ConsigneeAddress2', 'ConsigneeAddress3', 'ConsigneeAddress4', 'ConsigneeCITY', 'ConsigneeState',
                  'ConsigneePOSTCODE', 'ConsigneeISOCNTRYCODE', 'ConsigneeVAT', 'BUYERPO', 'CARRIERCODE', 'CARRIERNAME',
                  'CARRIERADDRESS1', 'CARRIERADDRESS2', 'CARRIERCITY', 'CARRIERSTATE', 'CARRIERPOSTCODE',
                  'CARRIERISOCNTRYCODE', 'CARRIERphone', 'UDF1', 'UDF2', 'UDF3', 'UDF4', 'UDF5', 'NOTES', 'NOTES2',
                  'Door', 'ExternLineNr', 'SKU', 'EachQTY', 'UoM', 'LOTTABLE01', 'LOTTABLE02', 'LOTTABLE03',
                  'LOTTABLE04', 'LOTTABLE05', 'LOTTABLE06', 'LOTTABLE07', 'LOTTABLE08', 'LOTTABLE09', 'LOTTABLE10',
                  'DETAIL_UDF1', 'DETAIL_UDF2', 'DETAIL_UDF3', 'DETAIL_UDF4', 'DETAIL_UDF5', 'DETAIL_NOTES',
                  'UnitPrice', 'PICKINGINSTRUCTIONS', 'UoMQty']
        list_data.append(header)
        ref = {}
        for item in data:
            self.list_obj_db.append(item)
            orderitem = OrderItems.objects.filter(magento_order=item.magento_order)
            for item_detail in orderitem:
                # Get Carrier Code
                skus = item_detail.item_id
                sku = [x for x in skus]
                input_data = ''.join(sku[:3])
                carrier_code = get_brand_vdc(input_data)
                print("carrier_code : ".format(carrier_code))
                if carrier_code == 'Not Match':
                    external_order = self.generate_order_id(item.channel, item_detail)
                else:
                    external_order = '{}{}'.format(carrier_code, self.generate_order_id(item.channel, item_detail))

                # Get ExternLineNr
                if self.generate_order_id(item.channel, item_detail) not in ref:
                    ref[self.generate_order_id(item.channel, item_detail)] = 1
                else:
                    ref[self.generate_order_id(item.channel, item_detail)] = ref[self.generate_order_id(item.channel, item_detail)] + 1

                rec = [
                    'GEO45', 'MIADPE001', external_order,
                    'EC', item_detail.order_date.split(" ")[0], item_detail.order_date.split(" ")[0], None, None, None,
                    item_detail.shipping_addressee, item_detail.shipping_address_line_1,
                    item_detail.shipping_address_line_2, None, None,
                    item_detail.shipping_address_city, item_detail.shipping_address_state_province,
                    item_detail.shipping_postal_code, item_detail.shipping_address_country, None, None,
                    carrier_code, None, None, None, None, None, None, None, None, item_detail.magento_order,
                    self.get_udf2(item.channel), self.payment_type(item_detail.payment_type), None, None, self.notes(item.channel), None,
                    None, '0000{}0'.format(ref[self.generate_order_id(item.channel, item_detail)]), item_detail.item_id,
                    item_detail.qty, 'EA', 'R', carrier_code, None, None, None, None, None, None, None, None, None,
                    'ZPL3_DO', None, item_detail.magento_order, None, None, None, None, None, None
                ]
                list_data.append(rec)
        return list_data
    
    def generate_file_name_agility(self):
        return self.agility_file_name

    def create_agility_data(self):
        """Create Agility Data"""
        now = datetime.now()
        data = self.get_data_for_agility()
        sheet_name = "Data"
        input_data = dict(
            sheet_name=sheet_name,
            payload=data
        )
        svc = GenerateXLS(input_data, self.generate_file_name_agility())
        print(f'Start Agility :{now}')
        print(f'Data : {data}')
        resp = svc.generate_xls(input_data, self.generate_file_name_agility())
        print(resp)

        return resp

    def save_sales_order_generated(self):
        for item_list in self.list_obj_db:
            item_list.agility_generated = True
            item_list.save()


class PurchaseOrder:
    def __init__(self):
        now = datetime.now()
        self.po_file_datetime = now.strftime('%Y%m%d%H%M%S%f')

    def generate_order_id(self, channel, content):
        order_id = ''
        if channel == 'map':
            order_id = 'PLSMEM_{}'.format(content['Magento Order #'])
        elif channel == 'lfc':
            order_id = 'PLSLFC_{}'.format(content['Order #'])
        elif channel == 'brooks':
            order_id = 'PLSBRO_{}'.format(content['Order #'])
        return order_id

    def generate_file_name(self, channel):
        file_name = ''
        if channel == 'map':
            file_name = 'MEM_{}.csv'.format(self.po_file_datetime)
        elif channel == 'lfc':
            file_name = 'LFC_{}.csv'.format(self.po_file_datetime)
        elif channel == 'brooks':
            file_name = 'BRO_{}.csv'.format(self.po_file_datetime)
        return file_name

    def generate_format_po(self, channel, order_data: list):
        """Generate Format Purchase Order"""
        content = []
        x = 0
        for item in order_data:
            if x < 1:
                header_format_po = [
                    'partnerPurchaseOrderId',
                    'partnerItemId',
                    'qty',
                    'unitPrice'
                ]
                content.append(header_format_po)
            order_id = self.generate_order_id(channel, item)
            format_po = [
                order_id,
                item['Item ID'],
                item['QTY'],
                item['Gross Total']
            ]
            content.append(format_po)
            x += 1
        return content

    def create_purchase_order(self, channel, order_data: list):
        """Create Purchase Order"""
        format_po = self.generate_format_po(channel, order_data)
        file_name = self.generate_file_name(channel)
        print(f'This is Purchase Order {channel}')
        print(f'Content Data Purchase Order {format_po}')
        svc = generate_csv(rows=format_po, filename=file_name)
        return svc.return_file_name()


def get_brand_vdc(input_code):
    """Brand for Agility File"""
    brand = Brand.objects.filter(code=input_code).first()
    print("Cari : {} di field code".format(input_code))
    print(brand)
    if brand is None:
        return 'Not Match'
    else:
        if brand.vdc.strip() is '':
            return 'Not Match'
        else:
            return brand.vdc


def salesorder_save_order(order_data: list, channel):
    """Save each order item to DB"""
    i = 0
    try:
        with transaction.atomic():
            for row in order_data:
                magento_order = ""
                if channel == 'map':
                    magento_order = row['Magento Order #']
                elif channel == "lfc":
                    magento_order = row['Order #']
                elif channel == "brooks":
                    magento_order = row['Order #']

                if i < 1:
                    Orders.objects.create(
                        magento_order=magento_order,
                        channel=channel
                    )
                OrderItems.objects.create(
                    oms_order=row['OMS Order#'],
                    magento_order=magento_order,
                    customer=row['Customer'],
                    payment_type=row['Payment Type'],
                    shipping_address_line_1=row['Shipping Address Line 1'],
                    shipping_address_line_2=row['Shipping Address Line 2'],
                    email=row['Email'],
                    gross_total=row['Gross Total'],
                    shipping_address_city=row['Shipping Address City'],
                    qty=row['QTY'],
                    collection_amount=row['Collection On Delivery Amount'],
                    shipping_address_state_province=row['Shipping Address State/Province'],
                    shipping_address_phone=row['Shipping Address Phone'],
                    shipping_addressee=row['Shipping Adressee'],
                    store_location=row['Store Loc'],
                    item_id=row['Item ID'],
                    tax_amount=row['Tax Amount'],
                    order_date=row['Order Date'],
                    shipping_type=row['Shipping Type'],
                    item=row['Item'],
                    payment_received=row['Payment Received'],
                    collection_on_delivery=row['Collection On Delivery (Y/N)'],
                    random_key=row['Random Key'],
                    shipping_address_country=row['Shipping Address Country'],
                    shipping_postal_code=row['Shipping Address Postal Code'],
                    price_before_tax=row['Price Before Tax'],
                    order_status='NEW'
                )
                i += 1

    except DatabaseError as err:
        logger.error("Exception when save data to database datamart. Error : {}".format(err))
        raise


def create_sales_order_cpms(order_data):
    """Push order data to CPMS"""
    cpms = CPMS()
    return cpms.create_order(order_data['orderId'], settings.CHANNEL_ID, order_data)


def check_order_in_cpms(order_id):
    cpms = CPMS()
    return cpms.check_order(order_id, settings.CHANNEL_ID)


def check_order_in_datamart(order_id):
    order = Orders.objects.filter(magento_order=order_id).first()
    return order

def order_id_column(channel):
    order_id = ''
    if channel == 'map':
        order_id = 'Magento Order #'
    elif channel == 'lfc':
        order_id = 'Order #'
    elif channel == 'brooks':
        order_id = 'Order #'
    return order_id


def filter_order_already_exists(channel, order_data):
    """Check if Order already exists create on CPMS and save to datamart"""
    data = []

    for row in order_data:
        order_id = row[order_id_column(channel)]
        cpms = check_order_in_cpms(order_id)
        datamart = check_order_in_datamart(order_id)
        if cpms['code'] == 200 or datamart is not None:
            logger.error(f'Order {order_id} Already Exists in CPMS and Datamart')
        else:
            data.append(row)

    return data

