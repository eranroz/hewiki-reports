"""Report on pages with work template"""
# -*- coding: utf-8 -*-
import datetime
import re

import pymysql as sql
import pywikibot

import settings

OLD_IN_WORK_PAGE = u'ויקיפדיה:ערכים שהוסרה מהם תבנית בעבודה/דפים עם התבנית'
FINISHED_WORK_PAGE = u'ויקיפדיה:ערכים שהוסרה מהם תבנית בעבודה'

site = pywikibot.Site()


def get_from_db():
    """Get the page info for pages containing template in work

    :return: Tuple of info report and list of pages
    """
    conn = sql.connect(host=settings.host,
                       db=settings.dbname,
                       read_default_file=settings.connect_file)  # , charset='utf8',use_unicode=True)

    resultText = u'{{/פתיח}}'
    cursor = conn.cursor()
    cursor.execute('''
        /* workTemplate.py SLOW_OK */
    SELECT page_title, actor_name, r.rev_timestamp from 
    (SELECT page_title, max(rev_id) as workRevId 
    FROM page p 
    INNER JOIN revision r
    ON p.page_id = r.rev_page 
    INNER JOIN actor
    ON rev_actor=actor_id
    WHERE p.page_namespace=0 
        AND p.page_id in (SELECT tl_from FROM templatelinks WHERE tl_title like 'בעבודה%' and tl_namespace=10)
        AND NOT EXISTS(select * from user_groups where ug_user=actor_user and ug_group='bot') 
        AND NOT EXISTS(select * from comment
            where (comment_text like '%שחזור%' or comment_text like '%שוחזר%') and r.rev_comment_id=comment_id)
        GROUP BY page_title
    ) work_page_rev
    INNER JOIN
         revision r on rev_id=workRevId 
        INNER JOIN actor
            ON rev_actor=actor_id
    ORDER BY r.rev_timestamp DESC
              ''')
    nowInWork = []
    for row in cursor.fetchall():
        days = (datetime.datetime.now() - datetime.datetime.strptime(row[2].decode('utf8'), "%Y%m%d%H%M%S")).days
        articleName = row[0].decode('utf-8').replace('_', ' ')
        resultText += u'\n#[[%s]] {{כ}} (%s, [[משתמש:%s]])' % (articleName, days, row[1].decode('utf-8'))
        nowInWork.append(articleName)
    cursor.close()
    conn.close()
    return resultText, nowInWork


def format_entry_finished(title, p_len, touched, categories):
    """Format for a single entry in the finished report

    :param title: page title
    :param p_len: page length
    :param touched: last touched time
    :param categories: categories
    :return: String representation for that entry
    """
    return u'| {{מעקב ערך|%s}}\n| %s || %s || %s' % (title.replace('_', ' '), p_len,
                                                     categories.replace('_', ' ').replace('[[',
                                                                                          u'[[:קטגוריה:'),
                                                     datetime.datetime.strptime(touched,
                                                                                '%Y%m%d%H%M%S').strftime(
                                                         '%Y-%m-%d %H:%M'))


def get_data_for_finished(articles):
    """Get additonal data for pages that are no longer in work

    :param articles: list of articles completed to work
    :return: Text for reporting these articles
    """
    conn = sql.connect(host=settings.host, db=settings.dbname, read_default_file=settings.connect_file, charset='utf8')
    titles = ','.join(["'%s'" % (conn.escape(x.replace(' ', '_').encode('utf-8'))) for x in articles])

    print(titles.encode('utf-8', 'replace').decode())
    cursor = conn.cursor()
    cursor.execute('''
    /* workTemplate.py SLOW_OK */
    select p.page_title, p.page_len,p.page_touched, GROUP_CONCAT( concat('[[',cl_to,'|]]') ORDER BY cl_to DESC SEPARATOR ', ')
    from categorylinks cl
    inner join page p
    on 
    p.page_id=cl.cl_from
    where p.page_title in (%s)
    group by p.page_title
    ''' % titles)

    decoded_res = []
    for title, pLen, touched, categories in cursor.fetchall():
        try:
            decoded_res.append((title.decode('utf-8'), pLen, touched, categories.decode('utf-8')))
        except:
            continue

    return '\n|-\n'.join([format_entry_finished(title, pLen, touched, categories) for
                          title, pLen, touched, categories in decoded_res])


def main():
    """
    Main report logic
    """
    log_finished_work = False  # TODO re-enable report on recently completed
    old_work = pywikibot.Page(site, OLD_IN_WORK_PAGE)
    old_in_work = [re.sub('# *\[\[(.*?)\]\].*', r'\1', x) for x in old_work.get().splitlines()[1:]]
    result_text, now_in_work = get_from_db()
    if log_finished_work:
        workFinished = [x for x in old_in_work if x not in now_in_work]
        print('Work finished: %i' % len(workFinished))
        finishFeed = get_data_for_finished(workFinished) if len(workFinished) > 0 else ''
        newPagesFinishedWorking = u'{{/פתיח}}\n|-\n%s\n' % finishFeed

        updatedPage = pywikibot.Page(site, FINISHED_WORK_PAGE)
        newUpdateText = updatedPage.get().replace(u'{{/פתיח}}\n', newPagesFinishedWorking)
        print(newPagesFinishedWorking)

        updatedPage.put(newUpdateText, summary=u'עדכון אוטומטי')
    old_work.put(result_text, summary=u'עדכון אוטומטי')


if __name__ == '__main__':
    main()
