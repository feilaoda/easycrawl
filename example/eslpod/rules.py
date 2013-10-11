
rules = [
    {
    'name'    : 'esl_data',
    'pattern' : 'show_podcast.php\\?issue_id=\\d+',
    'action'  : 'data',
    },
    
    {
    'name'    : 'esl_list',
    'pattern' : 'show_all.php\\?cat_id=-59456&low_rec=\\d+',
    'action'  : 'list',
    },

]

