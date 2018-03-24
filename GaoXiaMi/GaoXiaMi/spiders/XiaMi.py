# -*- coding: utf-8 -*-
import scrapy
import urlparse
import os
import re

from OurBaseSpider import OurBaseSpider
from GaoXiaMi.items import SongBasicItem
from GaoXiaMi.items import SongCommentItem




class XiamiSpider(OurBaseSpider):
    name = "xiami"
    allowed_domains = []
    start_urls = (
        'http://www.xiami.com/',
    )
    artist_url_set = set([])

    def parse(self, response):
        #debug  yield a request for 告白气球
        # print response.css('div #title h1').xpath("text()").extract_first("")
        #link = 'http://www.xiami.com/song/mQX8iP8fbe8'


        seed_links = [
            'http://www.xiami.com/artist/iim17edb'
        ]

        for link in seed_links:
            #print "xxx" * 300
            request = scrapy.Request(link, callback=self.parse_artist_page,
                                 headers={'Referer': response.url})
            yield request


        pass
        '''
        seed_links = [
            'http://www.xiami.com/song/9iYP3fba3'
        ]
        for link in seed_links:
            request = scrapy.Request(link, callback=self.parse_song_page,
                                     headers={'Referer': response.url})
            yield request
        '''

    def parse_artist_page(self, response):
        for url in response.css('div#artist_recommend ul li a').xpath('@href').extract():
            full_url = urlparse.urljoin(response.url, url)
            if full_url not in self.artist_url_set and len(self.artist_url_set) < self.settings['MAX_ARTIST_COUNT']:
                self.artist_url_set.add(full_url)
                request = scrapy.Request(full_url, callback=self.parse_artist_page,
                                         headers={'Referer': response.url})
                yield request

        top_link_text = response.css('div#artist_trends div.acts a').xpath('text()').extract_first('')
        top_link_url = response.css('div#artist_trends div.acts a').xpath('@href').extract_first('')
        if u'热门' in top_link_text:
            full_url = urlparse.urljoin(response.url, top_link_url)
            request = scrapy.Request(full_url, callback=self.parse_artist_top_songs,
                                     headers={'Referer': response.url})
            yield request

    def parse_artist_top_songs(self, response):
        # songs
        song_urls = response.css('table.track_list tr td.song_name a').xpath('@href').extract()
        for song_url in song_urls:
            if os.path.dirname(song_url) != '/song':
                continue
            full_song_url = urlparse.urljoin(response.url, song_url)
            request = scrapy.Request(full_song_url, callback=self.parse_song_page,
                                     headers={'Referer': response.url})
            yield request

        # next page
        next_url = response.css('a.p_redirect_l').xpath('@href').extract_first('')
        if next_url != '':
            full_next_url = urlparse.urljoin(response.url, next_url)
            request = scrapy.Request(full_next_url, callback=self.parse_artist_top_songs,
                                     headers={'Referer': response.url})
            yield request

    def parse_comments_page(self, response):
        cur_page = response.meta['page']
        s_item = response.meta['s_item']
        for li in response.css('ul li'):
            c_item = self.get_comment_item_from_li(li, s_item)
            yield c_item
        # 翻页处理:
        next_page_url = response.css("a.p_redirect_l").xpath('@href').extract_first('')
        if next_page_url != '':
            next_page_text = os.path.basename(next_page_url)
            try:
                next_page = int(next_page_text)
                if next_page > cur_page:# go to next page
                    next_page_url_ajax =  os.path.join(next_page_url, 'ajax/1')
                    full_next_page_url_ajax = urlparse.urljoin(response.url, next_page_url_ajax)
                    c_req = scrapy.http.FormRequest(full_next_page_url_ajax,
                        formdata={'type': '4'}, callback=self.parse_comments_page, meta={'page':next_page, 's_item':s_item})
                    yield c_req
            except Exception as e:
                self.logger.error(e)
        pass

    def parse_song_page(self, response):
        item = SongBasicItem()
        item['spider'] = self.name
        item['ori_id'] = os.path.basename(urlparse.urlparse(response.url).path)
        item['id'] = "%s_%s" % (item['spider'], item['ori_id'])
        item['name'] = response.css('div #title h1').xpath("text()").extract_first("")
        item['album'] = ''
        item['album_url'] = ''
        item['player'] = ''
        item['player_url'] = ''
        item['writer'] = ''
        item['composer'] = ''
        item['arranger'] = ''
        item['words'] = ''
        item['url'] = response.url
        item['n_comments'] = response.css("p.wall_list_count span").xpath("text()").extract_first()
        item['others'] = ''

        for tr in response.css('table#albums_info tr'):
            k = tr.css('td.item').xpath("text()").extract_first()
            v = "".join(tr.css('td div').xpath("descendant-or-self::*/text()").extract()).strip()
            url = tr.css('td div').xpath("descendant-or-self::*/@href").extract_first('')
            if u'专辑' in k:
                item['album'] = v
                item['album_url'] = urlparse.urljoin(response.url, url)
            elif u'演唱' in k:
                if url != '':
                    v_list = tr.css('td div a').xpath('text()').extract()
                    url_list = [ urlparse.urljoin(response.url, l) for l in tr.css('td div a').xpath('@href').extract()]
                    # 先入库第一个歌手
                    item['player'] = v_list[0]
                    item['player_url'] = url_list[0]
                else:
                    item['player'] = v.replace("\t", " ")
                    item['player_url'] = url
            elif u'作词' in k:
                item['writer'] = v
            elif u'作曲' in k:
                item['composer'] = v
            elif u'编曲' in k:
                item['arranger'] = v

        item['words'] =  "".join([i.strip() for i in response.css("div.lrc_main").xpath("text()").extract()])
        yield  item

        # hot comments
        for li in response.css("div.common_sec div.hotComment ul li"):
            citem = self.get_comment_item_from_hot_li(li, item)
            yield citem

        # comments on this page
        for li in response.css("div.common_sec div#wall_list ul li"):
            citem = self.get_comment_item_from_li(li, item)
            yield citem

        # yield comments requests for next page songs
        next_page_url = response.css("div.common_sec div#wall_list div.all_page a.p_redirect_l").xpath('@href').extract_first('')
        if next_page_url != '':
            cur_page = 1
            next_page_text = os.path.basename(next_page_url)
            try:
                next_page = int(next_page_text)
                if next_page > cur_page:# go to next page
                    next_page_url_ajax =  os.path.join(next_page_url, 'ajax/1')
                    full_next_page_url_ajax = urlparse.urljoin(response.url, next_page_url_ajax)
                    c_req = scrapy.http.FormRequest(full_next_page_url_ajax,
                                                    formdata={'type': '4'}, callback=self.parse_comments_page, meta={'page':next_page, 's_item':item})
                    yield c_req
            except Exception as e:
                self.logger.error(e)

    def get_comment_item_from_li(self, li, s_item):
        item = SongCommentItem()
        ori_id = li.xpath('@id').extract_first('')
        item['id'] = self.name + '_' +ori_id
        item['spider'] = self.name
        item['song_id'] = s_item['id']
        item['ori_song_id'] = s_item['ori_id']
        item['ori_parent_id'] = ''
        item['username'] = li.css("div.info span.author a").xpath('text()').extract_first('')
        item['user_url'] = li.css("div.info span.author a").xpath('@href').extract_first('')
        item['up_count'] = 0
        item['down_count'] = 0
        up_count_text = li.css("div.info span.ageree a").xpath('text()').extract_first('')
        down_count_text = li.css("div.info span.disageree a").xpath('text()').extract_first('')
        try:
            up_count = int(re.search(ur'\((\d+)\)', up_count_text).group(1))
            down_count = int(re.search(ur'\((\d+)\)', down_count_text).group(1))
            item['up_count'] = up_count
            item['down_count'] = down_count
        except Exception as e:
            self.logger.error(e)
        client_text = li.css("div.brief div a").xpath('text()').extract_first('')
        client = ''
        try:
            client_re = re.search(ur'来自(.*)客户端', client_text)
            if client_re != None:
                client = client_re.group(1)
        except Exception as e:
            self.logger.error("%s | client_text: [%s]" % (e, client_text))
            client = client_text.replace("\t", '').strip()[:20]
        item['client_agent'] = client
        item['post_datetime'] = li.css("div.info span.time").xpath('text()').extract_first('')
        item['is_hot'] = 0
        item['content'] = "".join([i.strip() for i in li.css("div.brief div").xpath('text()').extract_first('')])
        return item

    def get_comment_item_from_hot_li(self, li, s_item):
        item = SongCommentItem()
        ori_id = li.xpath('@id').extract_first('')
        item['id'] = self.name + '_' +ori_id
        item['spider'] = self.name
        item['song_id'] = s_item['id']
        item['ori_song_id'] = s_item['ori_id']
        item['ori_parent_id'] = ''
        item['username'] = li.css("div.info span.author a").xpath('text()').extract_first('')
        item['user_url'] = li.css("div.info span.author a").xpath('@href').extract_first('')
        item['up_count'] = 0
        item['down_count'] = 0
        up_count_text = li.css("div.info span.ageree a").xpath('text()').extract_first('')
        down_count_text = li.css("div.info span.disageree a").xpath('text()').extract_first('')
        try:
            up_count = int(re.search(ur'\((\d+)\)', up_count_text).group(1))
            down_count = int(re.search(ur'\((\d+)\)', down_count_text).group(1))
            item['up_count'] = up_count
            item['down_count'] = down_count
        except Exception as e:
            self.logger.error(e)
        item['client_agent'] = ''
        item['post_datetime'] = li.css("div.info span.time").xpath('text()').extract_first('')
        item['is_hot'] = 1
        item['content'] =  "".join([i.strip() for i in li.css("div.brief").xpath('descendant-or-self::text()').extract()])
        return item

