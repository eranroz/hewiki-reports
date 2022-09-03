"""Report on pages in draft namespace"""
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

import pymysql as sql  # MySQLdb
import pywikibot

import settings

PUBLISH_PAGE = 'ויקיפדיה:מרחב טיוטה/מעקב'
site = pywikibot.Site()


def format_entry(row):
    """Format each entry in the report

    :param row: A row from database query on a specific draft page
    :return: Text representation for that entry
    """
    title, timestamp, page_len, links = row
    title = title.decode('utf-8').replace('_', ' ')
    timestamp = datetime.datetime.strptime(timestamp, '%Y%m%d%H%M%S')

    return '{{{{/פריט|{}|{}|{}|{}}}}}'.format(title, timestamp, page_len, links)


def get_from_db():
    """Get pages from database from draft namespace, formatted for report

    :return: A text with report on the pages in draft database
    """
    with sql.connect(host=settings.host, db=settings.dbname, read_default_file=settings.connect_file) as cursor:
        # cursor = conn.cursor()
        cursor.execute('''
            /* draftWatch.py SLOW_OK */
            select page_title, rev_timestamp, page_len, 
            count(*) links
            from 
                page p 
            inner join 
                revision 
            on 
                p.page_latest=rev_id
            left join pagelinks 
            on 
                pl_from_namespace=0 and pl_namespace=0 and pl_title=page_title
            where 
                p.page_namespace=118 and p.page_is_redirect=0
            group by p.page_title
            order by rev_timestamp asc;
                  ''')
        res = map(format_entry, cursor.fetchall())
        # cursor.close()
        # conn.close()
        return '\n'.join(res)


def main():
    """
    Main report logic
    """
    drafts_data = get_from_db()
    page = pywikibot.Page(site, PUBLISH_PAGE)
    page_text = """{{{{/פתיח}}}}
    {}
    |}}""".format(drafts_data)
    page.put(page_text, summary='עדכון אוטומטי')


if __name__ == '__main__':
    main()
