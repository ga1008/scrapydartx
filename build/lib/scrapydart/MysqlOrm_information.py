import logging
from .model_news_infomation import SpiderMonitor, UnormalSpider, TerminatedSpider
from .model_news_infomation import session


class GetBDataBase(object):

    def __init__(self):
        super(GetBDataBase, self).__init__()

    def get_protogenesis(self, model, sql=None, where='', field=[]):
        field_str = ', '.join(field) if field else '*'
        if sql is None:
            wheres = where if where else ''
            sql = 'select %s from %s%s;' % (field_str, model.__tablename__, wheres)
        result = session.execute(sql).fetchall()
        model_map = [model(**dict(zip(x.keys(), x))) for x in result]
        return model_map

    def insert_data(self, model, field_names, values):
        if isinstance(field_names, str):
            field_names = [field_names]
        if not isinstance(values, (list, tuple)):
            values = [values]

        values = ['"{}"'.format(x) for x in values]
        values = ','.join(values)
        field_names = ",".join(field_names)
        # sql = "insert into {} set {}={};".format(model.__tablename__, field_names, values)
        sql = "insert into {}({}) values ({});".format(model.__tablename__, field_names, values)
        try:
            session.execute(sql)
            session.commit()
        except Exception as E:
            msg = """**** insert err: %s""" % E
            logging.error(msg)

    def get_spider_runtime(self, field, where=''):
        model_map = self.get_protogenesis(model=SpiderMonitor, where=where, field=field)
        return model_map

    def get_unormal_spider(self, field, where=''):
        model_map = self.get_protogenesis(model=UnormalSpider, where=where, field=field)
        return model_map

    def get_terminated_spider(self, field, where=''):
        model_map = self.get_protogenesis(model=TerminatedSpider, where=where, field=field)
        return model_map
