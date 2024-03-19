import mysql.connector


SECRET_KEY = 'fc7a31a759d6ebdcb3076fb77c0fb02c8fd970850de91323d4e74b14e9fa1377'
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120
CONNECTION = mysql.connector.connect(
  host="localhost",
  user="root",
  password="!7EE5#Pe1d@J",
  port="3306",
  database='AtlasDB'
)

CURSOR = CONNECTION.cursor()