# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class GaoxiamiItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class SongBasicItem(scrapy.Item):
    # define the fields for your item here like:
    id = scrapy.Field()
    spider = scrapy.Field()
    ori_id = scrapy.Field()
    name = scrapy.Field()
    url = scrapy.Field()
    album = scrapy.Field()
    album_url = scrapy.Field()
    player = scrapy.Field()
    player_url = scrapy.Field()
    writer = scrapy.Field()
    composer = scrapy.Field()
    arranger = scrapy.Field()
    n_comments = scrapy.Field()
    words = scrapy.Field()
    others = scrapy.Field()
    pass

class SongCommentItem(scrapy.Item):
    # define the fields for your item here like:
    id = scrapy.Field()
    spider = scrapy.Field()
    song_id = scrapy.Field()
    ori_song_id = scrapy.Field()
    ori_parent_id = scrapy.Field()
    username = scrapy.Field()
    user_url = scrapy.Field()
    up_count = scrapy.Field()
    down_count = scrapy.Field()
    client_agent = scrapy.Field()
    post_datetime = scrapy.Field()
    is_hot = scrapy.Field()
    content = scrapy.Field()
    pass
