import logging
from scrapydartx.mysql_models import SpiderMonitor, UnormalSpider, TerminatedSpider
from scrapydartx.mysql_models import session


class GetData:

    def __init__(self):
        super(GetData, self).__init__()

    def get_protogenesis(self, model, sql=None, where='', field=[]):
        try:
            session.commit()
        except Exception as E:
            logging.warning('start commit fail : {}'.format(E))
        field_str = ', '.join(field) if field else '*'
        if sql is None:
            wheres = where if where else ''
            sql = 'select %s from %s%s;' % (field_str, model.__tablename__, wheres)
        result = session.execute(sql).fetchall()
        model_map = [model(**dict(zip(x.keys(), x))) for x in result]
        return model_map

    def insert_data(self, model, field_names, values):
        try:
            session.commit()
        except Exception as E:
            logging.warn('start commit fail : {}'.format(E))
        if isinstance(field_names, str):
            field_names = [field_names]
        if not isinstance(values, (list, tuple)):
            values = [values]

        values = ['"{}"'.format(x) for x in values]
        values = ','.join(values)
        field_str = ",".join(field_names)
        sql = "insert into {}({}) values ({});".format(model.__tablename__, field_str, values)
        try:
            session.execute(sql)
            session.commit()
            return True
        except Exception as E:
            msg = """**** insert err: %s""" % E
            logging.error(msg)
            return False

    def get_spider_runtime(self, field, where=''):
        model_map = self.get_protogenesis(model=SpiderMonitor, where=where, field=field)
        return model_map

    def get_unormal_spider(self, field, where=''):
        model_map = self.get_protogenesis(model=UnormalSpider, where=where, field=field)
        return model_map

    def get_terminated_spider(self, field, where=''):
        model_map = self.get_protogenesis(model=TerminatedSpider, where=where, field=field)
        return model_map

    def get_result(self, model, fields=None, where_dic=None, sql=None, return_model_map=True):
        """
        :param model:
        :param fields:
        :param where_dic:   {'key1': '=*value1', 'key2': '>*value2'}
        :param sql:
        :param return_model_map:
        :return:
        """
        try:
            session.commit()
        except Exception as E:
            logging.warning('start commit fail : {}'.format(E))
        if sql is None:
            if isinstance(fields, str):
                field_str = fields
            else:
                field_str = ','.join(fields) if fields else '*'
            wheres = '' if where_dic is None else ' where ' + ' and '.join(['{}{}"{}"'.format(x, where_dic.get(x).split('*')[0], where_dic.get(x).split('*')[1]) for x in where_dic])
            sql = 'select %s from %s%s;' % (field_str, model.__tablename__, wheres)
        result = session.execute(sql).fetchall()
        if return_model_map:
            model_map = [model(**dict(zip(x.keys(), x))) for x in result]
            return model_map
        else:
            return result

    def del_data(self, model, where_dic=None):
        """
        :param model:
        :param where_dic:  {'key1': [value11, value12, ...], 'key2': [value21]}
        :return:
        """
        try:
            session.commit()
        except Exception as E:
            logging.warning('start commit fail : {}'.format(E))
        where_str = ''
        if where_dic:
            where_or_lis = list()
            for where_key in where_dic:
                where_temp = ' or '.join(['{}="{}"'.format(where_key, x) for x in where_dic.get(where_key)])
                where_temp = '({})'.format(where_temp)
                where_or_lis.append(where_temp)
            where_str = ' where ' + ' and '.join(where_or_lis)
        sql = 'delete from {}{};'.format(model.__tablename__, where_str)
        try:
            session.execute(sql)
            session.commit()
        except Exception as E:
            msg = """**** delete err: %s""" % E
            logging.error(msg)

    def update_data(self, model, set_dic, where_dic=None, where_combine_method='and'):
        # 'UPDATE cs_user SET gender = "" WHERE id = 4'
        set_raw = ['{}="{}"'.format(x, set_dic.get(x)) for x in set_dic]
        set_str = ','.join(set_raw)
        where_str = ''
        if where_dic is not None:
            where_raw = ['{}="{}"'.format(y, set_dic.get(y)) for y in where_dic]
            where_str = ' {} '.format(where_combine_method).join(where_raw)
            where_str = ' where ' + where_str
        sql = "update {} set {}{};".format(model.__tablename__, set_str, where_str)
        try:
            session.execute(sql)
            session.commit()
        except Exception as E:
            msg = """**** update err: %s""" % E
            logging.error(msg)


if __name__ == "__main__":
    db = GetData()
    db.del_data(
            model=SpiderMonitor,
            where_dic={
                'project': ['P1'],
                'id': [1]
            }
    )