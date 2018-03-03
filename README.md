KUMPARAN API NEWS

1. Add News
   POST <base URL>/api/news/add

2. Delete News
   GET <base URL>/api/news/<id news>/delete

2. Filter List News
   GET <base URL>/api/news?status=<status news>&topic=<topic news>


Prerequisites:
- virtual env python 3.6
- postgresql
- edit .env to align with your environment

Running the unit test :
- activate the virtual env python 3.6
- run db migrate : python3.6 manage migrate
- run : python3.6 manage test