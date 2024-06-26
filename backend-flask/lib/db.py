from psycopg_pool import ConnectionPool
import os
import re
import sys
from flask import current_app as app





class Db:
  def __init__(self):
    self.init_pool()

  def template(self,*args):
    pathing = list((app.root_path,'db','sql',) + args)
    pathing[-1] = pathing[-1] + ".sql"
    template_path = os.path.join(*pathing)

    green = '\033[92m'
    no_color = '\033[0m'
    print("\n")
    print(f'{green} Load SQL Template: {template_path} {no_color}')

    with open(template_path, 'r') as f:
      template_content = f.read()
    return template_content
  
  def init_pool(self):
    connection_url = os.getenv("CONNECTION_URL")
    self.pool = ConnectionPool(connection_url)

  def print_params(self,params):
    blue = '\033[94m'
    no_color = '\033[0m'
    print(f'{blue} SQL Params:{no_color}')
    for key, value in params.items():
      print(key, ":", value)

  def print_sql(self, title, sql, params={}):
    print("\n")
    cyan = '\033[96m'
    no_color = '\033[0m'
    print(f'{cyan}SQL STATEMENT [{title}]------------{no_color}')
    print(sql, params)
  # we want to commit data such as insert
  # check for uppercase RETURNING
  def query_commit(self, sql, params={},verbose=True):
    if verbose:
      print('commit', sql, params)

    pattern = r"\bRETURNING\b"
    is_returning_id = re.search(pattern, sql)
    self.print_sql('commit with returning', sql)
    print('SQL STATEMENT END [commit with returning]-----------')
    try:
      with self.pool.connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        if is_returning_id:
          returning_id = cur.fetchone()[0]
        conn.commit()
        if is_returning_id:
          return returning_id
    except Exception as err:
      self.print_sql_err(err)

  # when we want to return a a single value
  def query_value(self, sql, params={},verbose=True):
    if verbose:
     self.print_sql('value',sql,params)

    with self.pool.connection() as conn:
      with conn.cursor() as cur:
        cur.execute(sql,params)
        json = cur.fetchone()
        return json[0]
  
  # when we want to return an array of json objects
  def query_array_json(self, sql, params={},verbose=True):
    if verbose:
      self.print_sql('array', sql, params)
    print(sql)
    print('SQL END [array]-----------')

    wrapped_sql = self.query_wrap_array(sql)
    with self.pool.connection() as conn:
      with conn.cursor() as cur:
        cur.execute(wrapped_sql, params)
        # this will return a tuple
        # the first field being the data
        json = cur.fetchone()
        return json[0]

  # when we want to return a json object
  def query_object_json(self, sql, params={},verbose=True):
    if verbose:
      self.print_sql('json', sql, params)
    print(sql)
    print('SQL END \\{object\\}-----------')

    wrapped_sql = self.query_wrap_object(sql)
    with self.pool.connection() as conn:
      with conn.cursor() as cur:
        cur.execute(wrapped_sql, params)
        json = cur.fetchone()
        if json == None:
          return "{}"
        else:
          return json[0]


    
  # define a function that handles and parses psycopg2 exceptions
  def query_wrap_object(self, template):
    sql = f"""
    (SELECT COALESCE(row_to_json(object_row),'{{}}'::json) FROM (
    {template}
    ) object_row);
    """
    return sql

  def query_wrap_array(self, template):
    sql = f"""
    (SELECT COALESCE(array_to_json(array_agg(row_to_json(array_row))),'[]'::json) FROM (
    {template}
    ) array_row);
    """
    return sql
    
  def print_sql_err(self, err):
    # get details about the exception
    err_type, err_obj, traceback = sys.exc_info()

    # get the line number when exception occured
    line_num = traceback.tb_lineno

    # print the connect() error
    print ("\npsycopg2 ERROR:", err, "on line number:", line_num)
    print ("psycopg2 traceback:", traceback, "-- type:", err_type)

    # psycopg2 extensions.Diagnostics object attribute
    # print ("\nextensions.Diagnostics:", err.diag)

    # print the pgcode and pgerror exceptions
    print ("pgerror:", err.pgerror)
    print ("pgcode:", err.pgcode, "\n")



db = Db()