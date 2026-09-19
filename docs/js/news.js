
/* =========================================================
   页面导航
========================================================= */

function goHome(page = 'home') {

    window.location.href =
        `../?page=${page}`;

}



/* =========================================================
   新闻状态
========================================================= */

let newsData = [];

let currentCategory = 'all';

let currentKeyword = '';

let autoRefresh = true;

let refreshTimer = null;



/* =========================================================
   模拟新闻数据
   后续替换成 API
========================================================= */

const mockNews = [

    {
        id: 1,
        title: 'A股市场午间重要资讯汇总',
        summary: '市场今日出现多个热点方向，科技、半导体及人工智能板块受到关注。',
        source: 'STOCK LAB',
        time: '10:31',
        category: 'market',
        level: 'important',
        stocks: ['000001', '600519'],
        tags: ['市场', 'A股']
    },

    {
        id: 2,
        title: '半导体产业链出现新的市场动态',
        summary: '产业链相关公司业务进展受到市场关注。',
        source: '财经资讯',
        time: '10:28',
        category: 'industry',
        level: 'normal',
        stocks: ['688981'],
        tags: ['半导体']
    },

    {
        id: 3,
        title: '政策层面释放新的产业发展信号',
        summary: '相关政策可能对产业链企业产生中长期影响。',
        source: '政策信息',
        time: '10:25',
        category: 'policy',
        level: 'important',
        stocks: [],
        tags: ['政策']
    },

    {
        id: 4,
        title: 'AI产业链公司最新业务进展',
        summary: '人工智能、算力及服务器方向受到资金关注。',
        source: 'RSS Feed',
        time: '10:21',
        category: 'technology',
        level: 'normal',
        stocks: ['000977'],
        tags: ['AI', '算力']
    },

    {
        id: 5,
        title: '上市公司发布最新公告',
        summary: '公司公告涉及业务合作及经营情况变化。',
        source: '公司公告',
        time: '10:18',
        category: 'announcement',
        level: 'important',
        stocks: ['600000'],
        tags: ['公告']
    },

    {
        id: 6,
        title: '海外市场最新消息',
        summary: '海外市场变化可能影响A股相关产业链。',
        source: 'RSS Feed',
        time: '10:15',
        category: 'global',
        level: 'normal',
        stocks: [],
        tags: ['海外']
    }

];



/* =========================================================
   初始化
========================================================= */

document.addEventListener(
    'DOMContentLoaded',
    () => {

        newsData = [...mockNews];

        renderNews();

        renderImportantNews();

        bindNewsSearch();

        bindCategories();

        startAutoRefresh();

        updateLastUpdate();

    }
);



/* =========================================================
   新闻列表
========================================================= */

function renderNews() {

    const container =
        document.getElementById('newsList');

    if (!container) {
        return;
    }


    let data =
        newsData.filter(news => {

            const categoryMatch =
                currentCategory === 'all' ||
                news.category === currentCategory;

            const keyword =
                currentKeyword.toLowerCase();

            const keywordMatch =
                !keyword ||
                news.title.toLowerCase().includes(keyword) ||
                news.summary.toLowerCase().includes(keyword) ||
                news.source.toLowerCase().includes(keyword) ||
                news.tags.some(
                    tag =>
                        tag.toLowerCase().includes(keyword)
                );

            return categoryMatch && keywordMatch;

        });


    container.innerHTML = '';


    data.forEach(news => {

        const article =
            document.createElement('article');

        article.className =
            'news-card';


        if (news.level === 'important') {
            article.classList.add('important');
        }


        article.innerHTML = `

            <div class="news-card-time">
                ${news.time}
            </div>

            <div class="news-card-content">

                <div class="news-card-top">

                    <span class="news-category-tag">
                        ${getCategoryName(news.category)}
                    </span>

                    ${news.level === 'important'
                ? '<span class="important-tag">重要</span>'
                : ''
            }

                </div>

                <h3>
                    ${news.title}
                </h3>

                <p>
                    ${news.summary}
                </p>

                <div class="news-card-meta">

                    <span>
                        ${news.source}
                    </span>

                    ${news.stocks.length
                ? `
                                <span>
                                    ${news.stocks.join(' · ')}
                                </span>
                              `
                : ''
            }

                </div>

            </div>

            <div class="news-card-arrow">
                →
            </div>

        `;


        article.addEventListener(
            'click',
            () => {

                openNews(news.id);

            }
        );


        container.appendChild(article);

    });


    const count =
        document.getElementById('newsResultCount');

    if (count) {

        count.textContent =
            `${data.length} 条资讯`;

    }

}



/* =========================================================
   重要新闻
========================================================= */

function renderImportantNews() {

    const container =
        document.getElementById(
            'importantNewsList'
        );

    if (!container) {
        return;
    }


    const important =
        newsData.filter(
            news => news.level === 'important'
        );


    container.innerHTML = '';


    important.forEach(news => {

        const item =
            document.createElement('div');

        item.className =
            'important-news-item';


        item.innerHTML = `

            <span class="important-news-dot"></span>

            <div>

                <strong>
                    ${news.title}
                </strong>

                <small>
                    ${news.time} · ${news.source}
                </small>

            </div>

        `;


        item.addEventListener(
            'click',
            () => openNews(news.id)
        );


        container.appendChild(item);

    });

}



/* =========================================================
   分类
========================================================= */

function bindCategories() {

    document
        .querySelectorAll('.news-category')
        .forEach(button => {

            button.addEventListener(
                'click',
                () => {

                    document
                        .querySelectorAll('.news-category')
                        .forEach(item => {

                            item.classList.remove(
                                'active'
                            );

                        });


                    button.classList.add(
                        'active'
                    );


                    currentCategory =
                        button.dataset.category ||
                        'all';


                    renderNews();

                }
            );

        });

}



/* =========================================================
   搜索
========================================================= */

function bindNewsSearch() {

    const input =
        document.getElementById('newsSearch');


    if (input) {

        input.addEventListener(
            'input',
            () => {

                currentKeyword =
                    input.value.trim();

                renderNews();

            }
        );

    }


    const clear =
        document.getElementById(
            'clearNewsSearch'
        );


    if (clear) {

        clear.addEventListener(
            'click',
            () => {

                input.value = '';

                currentKeyword = '';

                renderNews();

                input.focus();

            }
        );

    }

}



/* =========================================================
   分类名称
========================================================= */

function getCategoryName(category) {

    const map = {

        market: '市场',
        company: '公司',
        industry: '行业',
        policy: '政策',
        announcement: '公告',
        global: '海外',
        technology: '科技',
        macro: '宏观'

    };


    return map[category] || '资讯';

}



/* =========================================================
   打开新闻
========================================================= */

function openNews(id) {

    console.log(
        '打开新闻:',
        id
    );

    /*
        后续这里可以：
 
        1. 打开 news/detail.html?id=xxx
 
        2. 或者：
 
           window.location.href =
               `./detail.html?id=${id}`;
 
        3. API 获取完整文章
 
        4. AI 摘要
 
        5. 股票关联
 
    */

}



/* =========================================================
   刷新
========================================================= */

function refreshNews() {

    console.log(
        '刷新新闻数据'
    );


    /*
        后续：
 
        fetch('/api/news/latest')
 
        ↓
 
        Python 后端
 
        ↓
 
        RSSFeedManager
 
        ↓
 
        数据库
 
        ↓
 
        JSON
 
    */


    updateLastUpdate();

}



/* =========================================================
   自动刷新
========================================================= */

function startAutoRefresh() {

    if (refreshTimer) {

        clearInterval(
            refreshTimer
        );

    }


    refreshTimer =
        setInterval(
            () => {

                if (autoRefresh) {

                    refreshNews();

                }

            },
            60000
        );

}



function toggleAutoRefresh() {

    autoRefresh =
        !autoRefresh;


    const button =
        document.getElementById(
            'autoRefreshButton'
        );


    if (button) {

        button.textContent =
            autoRefresh
                ? '自动刷新：开启'
                : '自动刷新：关闭';

    }

}



/* =========================================================
   更新时间
========================================================= */

function updateLastUpdate() {

    const element =
        document.getElementById(
            'lastUpdateText'
        );


    if (!element) {
        return;
    }


    const now =
        new Date();


    element.textContent =
        `最后更新 ${now.toLocaleTimeString(
            'zh-CN',
            {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            }
        )}`;

}



/* =========================================================
   加载更多
========================================================= */

function loadMoreNews() {

    console.log(
        '加载更多新闻'
    );


    /*
        后续 API：
 
        /api/news?page=2
 
    */

}



/* =========================================================
   全部已读
========================================================= */

function markAllRead() {

    document
        .querySelectorAll(
            '.news-card.unread'
        )
        .forEach(
            item => {
                item.classList.remove(
                    'unread'
                );
            }
        );


    const unread =
        document.getElementById(
            'unreadCount'
        );


    if (unread) {

        unread.textContent =
            '0';

    }

}



/* =========================================================
   搜索框
========================================================= */

function focusNewsSearch() {

    const input =
        document.getElementById(
            'newsSearch'
        );


    if (input) {

        input.focus();

        input.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });

    }

}

/* =========================================================
资讯入口
========================================================= */

function openExternalSource(source) {

    if (source === 'x') {

        /*
            后续可以接自己的 X 信息流页面。
            目前先作为入口占位。
        */

        console.log('打开 X 信息流');

        return;
    }

}


function selectNewsSource(source) {

    const categoryMap = {

        finance: 'market',

        announcement: 'announcement',

        policy: 'policy'

    };


    const category =
        categoryMap[source];


    if (!category) {
        return;
    }


    const button =
        document.querySelector(
            `.news-category[data-category="${category}"]`
        );


    if (button) {

        button.click();

        button.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });

    }

}
