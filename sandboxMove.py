"""Report on pages in draft namespace"""
# -*- coding: utf-8 -*-
import datetime
import re
import pywikibot
import pymysql as sql  # MySQLdb
import settings

FINISHED_WORK_PAGE = u'ויקיפדיה:ערכים חדשים'

site = pywikibot.Site()


def get_recent_moves(from_time):
    """Get the moved pages since desired time.

    :return: Tuple of moved articles
    """
    conn = sql.connect(host=settings.host,
                       db=settings.dbname,
                       read_default_file=settings.connect_file)
    start_date = from_time.strftime('%Y-%m-%d %H:%M:%S')
    date_limit = "STR_TO_DATE('%s'" % start_date + ",'%Y-%m-%d %H:%i:%s')"
    cursor = conn.cursor()
    cursor.execute('''
        /* sandboxMove.py SLOW_OK */
        SELECT page_title, actor_name, page_len,
        GROUP_CONCAT( concat('[[',cl_to,'|]]') ORDER BY cl_to DESC SEPARATOR ', '),
        log_timestamp -- do we need log params
        from logging
        inner join actor on log_actor=actor_id
        inner join page on log_page=page_id
        inner join categorylinks cl on log_page=cl.cl_from
        where log_type ='move' and log_namespace > 0 and log_timestamp>%s 
            and page_namespace=0 
            and not exists(select * from page_props, page cat_page
             where pp_page=cat_page.page_id and cat_page.page_namespace=14 and
             cat_page.page_title=cl_to and pp_propname='hiddencat')
            group by page_title order by log_timestamp DESC
              ''' % date_limit)

    moved_pages = []

    for title, user, page_len, cats, timestamp in cursor.fetchall():
        articleName = title.decode('utf-8').replace('_', ' ')
        timestamp = datetime.datetime.strptime(timestamp.decode('utf-8'), '%Y%m%d%H%M%S')
        user = user.decode('utf-8')
        cats = cats.decode('utf-8').replace('_', ' ').replace('[[', u'[[:קטגוריה:')
        moved_pages.append((articleName, user, page_len, cats, timestamp))
    cursor.close()
    conn.close()
    return moved_pages


def main():
    """
    Main report logic
    """
    updatedPage = pywikibot.Page(site, FINISHED_WORK_PAGE)
    moves_data = get_recent_moves(
        updatedPage.editTime() - datetime.timedelta(days=2))  # datetime.datetime.now()-datetime.timedelta(days=2)
    oldUpdateText = updatedPage.get()
    alreadyIn = set(re.findall(u'{{מעקב ערך\|(.*?)}}', oldUpdateText))
    moves_data_new = [p for p in moves_data if p[0] not in alreadyIn]

    if len(moves_data_new) > 0:
        entries = []
        for title, user, page_len, cats, timestamp in moves_data_new:
            entry_format = '| {{מעקב ערך|%s}}\n| [[משתמש:%s|]] || %s || %s || %s' % (
                title, user, page_len, cats, timestamp.strftime('%Y-%m-%d %H:%M'))
            entries.append(entry_format)
        finishFeed = '\n|-\n'.join(entries)
        if len(finishFeed) > 0:
            newPagesFinishedWorking = u'{{/פתיח}}\n|-\n%s\n' % finishFeed
            newUpdateText = oldUpdateText.replace(u'{{/פתיח}}', newPagesFinishedWorking)
            updatedPage.put(newUpdateText, summary=u'עדכון אוטומטי')
        # print(newUpdateText)


if __name__ == '__main__':
    main()
