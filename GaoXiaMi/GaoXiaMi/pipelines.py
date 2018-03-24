# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import logging
from GaoXiaMi.items import SongBasicItem
from GaoXiaMi.items import SongCommentItem
from GaoXiaMi.lib import database


class GaoxiamiPipeline(object):
    def process_item(self, item, spider):
        return item

class MysqlPipeline(object):
    """
        处理和临时DB的交互的pipeline,入库
    """
    def __init__(self, settings):
        logging.info("=" * 20 + "MysqlPipeline in open_spider" + "=" * 20)
        self.db_config = settings.get('DB_CONFIG')
        self.conn = None

    def open_spider(self, spider):
        self.conn = database.Connection(**self.db_config)
        pass

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            #db_config=crawler.settings.get('DB_CONFIG')
            settings=crawler.settings
        )

    def process_item(self, item, spider):
        """check format and insert it into DB"""
        if type(item) == SongBasicItem:
            keys = ['id', 'spider', 'ori_id', 'name', 'url', 'album', 'album_url',
                    'player', 'player_url', 'writer', 'composer', 'arranger', 'n_comments', 'words', 'others']
            keys_str = ",".join(["`%s`" % (k) for k in keys])
            s_str = ", ".join(["%s"] * len(keys))
            keys_value_list = [item[k] for k in keys]

            sql = '''INSERT INTO `song_basic` (%s) values (%s) on duplicate key update `n_comments`=VALUES(`n_comments`),  `words`=VALUES(`words`)''' % (keys_str, s_str)

            try:
                ret = self.conn.execute(sql, *keys_value_list)
                spider.logger.info("dump item[%s] into DB" % (item['id']))
            except Exception:
                spider.logger.error("insert item to DB error, sql[%s][%s]" % (sql, item), exc_info=True)
            return item
        elif type(item) == SongCommentItem:

            keys = ['id', 'spider', 'song_id', 'ori_song_id', 'ori_parent_id', 'username', 'user_url',
                    'up_count', 'down_count', 'client_agent', 'post_datetime', 'is_hot', 'content']
            keys_str = ",".join(["`%s`" % (k) for k in keys])
            s_str = ", ".join(["%s"] * len(keys))
            keys_value_list = [item[k] for k in keys]

            if item['is_hot'] != 1:
                sql = ('''INSERT INTO `song_comments` (%s) values (%s) on duplicate key update `up_count`=VALUES(`up_count`), '''
                    '''`down_count`=VALUES(`down_count`)''') % (keys_str, s_str)
            else:
                sql = ('''INSERT INTO `song_comments` (%s) values (%s) on duplicate key update `up_count`=VALUES(`up_count`), '''
                '''`down_count`=VALUES(`down_count`), `is_hot`=VALUES(`is_hot`)''') % (keys_str, s_str)

            try:
                ret = self.conn.execute(sql, *keys_value_list)
                spider.logger.info("dump item[%s] into DB" % (item['id']))
            except Exception:
                spider.logger.error("insert item to DB error, sql[%s][%s]" % (sql, item), exc_info=True)
            return item

    def close_spider(self, spider):
        logging.info("=" * 20 + "MysqlPipeline in close_spider" + "=" * 20)
        self.conn.close()
