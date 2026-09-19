/*
 * =========================================================
 * YouTube Intelligence
 * =========================================================
 *
 * 所有数据通过后端 Python API 获取。
 *
 * 前端：
 *
 * HTML
 *   ↓
 * youtube.js
 *   ↓
 * FastAPI
 *   ↓
 * YouTubeService
 *   ↓
 * YouTubeMonitor
 *   ↓
 * YouTube Data API
 *
 * 前端不直接访问 YouTube API。
 * API Key 永远只存在后端。
 *
 * =========================================================
 */


const API_BASE = '/api/youtube';


let currentCategory = 'all';

let refreshTimer = null;


/* =========================================================
   初始化
   ========================================================= */

document.addEventListener(
    'DOMContentLoaded',
    () => {

        loadAllData();

        /*
         * 前端只负责刷新显示。
         *
         * 真正的 YouTube 抓取任务由
         * Python 后台负责。
         *
         * 这里每 30 秒重新读取一次后端缓存。
         */

        refreshTimer = setInterval(
            loadLiveData,
            30000
        );

    }
);


/* =========================================================
   初始加载
   ========================================================= */

async function loadAllData() {

    await Promise.allSettled([

        loadStatus(),

        loadChannels(),

        loadVideos(),

        loadAIRanking(),

        loadConfig()

    ]);

}


/* =========================================================
   动态刷新
   ========================================================= */

async function loadLiveData() {

    await Promise.allSettled([

        loadStatus(),

        loadVideos(),

        loadAIRanking()

    ]);

}


/* =========================================================
   通用 GET
   ========================================================= */

async function apiGet(path) {

    const response = await fetch(
        API_BASE + path,
        {
            method: 'GET',
            cache: 'no-store'
        }
    );


    if (!response.ok) {

        throw new Error(
            `HTTP ${response.status}`
        );

    }


    const result =
        await response.json();


    if (result.success === false) {
        throw new Error(
            result.message ||
            'API 请求失败'
        );

    }


    /*
     * FastAPI 统一返回：
     *
     * {
     *     success: true,
     *     data: ...
     * }
     *
     * 前端直接使用 data。
     */

    return result.data;

}


/* =========================================================
   状态
   ========================================================= */

async function loadStatus() {

    try {

        const data =
            await apiGet('/status');

        if (
            data.channelCount !== undefined
        ) {
            document.getElementById(
                'channelCount'
            ).textContent =
                data.channelCount;

        }


        if (
            data.todayVideoCount !== undefined
        ) {

            document.getElementById(
                'videoCount'
            ).textContent =
                data.todayVideoCount;
        }

        if (
            data.interval !== undefined
        ) {

            updateIntervalDisplay(
                Number(data.interval)
            );

        }


        if (
            data.api_status !== undefined
        ) {

            updateAPIStatus(
                data.api_status
            );

        }


        if (
            data.monitoring !== undefined
        ) {

            updateMonitorStatus(
                data.monitoring
            );

        }


        if (
            data.last_check
        ) {

            document.getElementById(
                'lastCheck'
            ).textContent =
                '最后检查：' +
                formatTime(
                    data.last_check
                );

        }

    } catch (error) {

        console.warn(
            '无法读取 YouTube 状态：',
            error
        );


        document.getElementById(
            'apiMetric'
        ).textContent =
            'OFFLINE';

    }

}


/* =========================================================
   API 状态
   ========================================================= */

async function testAPI() {

    const button =
        document.querySelector(
            '.yt-secondary'
        );


    button.disabled = true;

    button.textContent =
        '测试中...';


    try {

        const data =
            await apiGet('/api-status');


        const status =
            data.status ||
            data.youtube_api ||
            data.api_status;


        if (
            status === 'ok' ||
            status === 'active' ||
            data.configured === true
        ) {

            button.textContent =
                '✓ API 正常';

        } else {

            button.textContent =
                '⚠ API 检查';

        }


        updateAPIStatus(
            status
        );


        await loadStatus();

    } catch (error) {

        console.warn(
            'API 测试失败：',
            error
        );


        button.textContent =
            '× API 异常';

    }


    setTimeout(
        () => {

            button.disabled = false;

            button.textContent =
                'API 测试';

        },
        1500
    );

}


/* =========================================================
   频道
   ========================================================= */

async function loadChannels() {

    try {

        const channels =
            await apiGet('/channels');


        renderChannels(
            Array.isArray(channels)
                ? channels
                : []
        );


        document.getElementById(
            'channelCount'
        ).textContent =
            channels.length;


        document.getElementById(
            'channelCacheStatus'
        ).textContent =
            `JSON CACHE · ${channels.length} CHANNELS`;

    } catch (error) {

        console.warn(
            '无法读取频道配置：',
            error
        );

    }

}


/* =========================================================
   渲染频道
   ========================================================= */

function renderChannels(channels) {

    const container =
        document.getElementById(
            'channelRows'
        );


    if (!channels.length) {

        container.innerHTML = `
            <div class="channel-row">

                <div class="channel-name">
                    暂无监控频道
                </div>

                <div class="channel-id">
                    —
                </div>

                <div class="channel-category">
                    —
                </div>

                <div class="channel-status">
                    EMPTY
                </div>

                <button
                    class="channel-action"
                    onclick="openChannelDialog()"
                >
                    添加
                </button>

            </div>
        `;

        return;

    }


    container.innerHTML =
        channels
            .map(
                channel => `

                    <div
                        class="channel-row"
                        data-category="${escapeHTML(
                    channel.category || ''
                )}"
                    >

                        <div class="channel-name">

                            ${escapeHTML(
                    channel.name || '—'
                )}

                        </div>


                        <div class="channel-id">

                            ${escapeHTML(
                    channel.channel_id || '—'
                )}

                        </div>


                        <div class="channel-category">

                            ${categoryLabel(
                    channel.category
                )}

                        </div>


                        <div class="channel-status">

                            ${channel.enabled === false
                        ? 'DISABLED'
                        : 'ACTIVE'
                    }

                        </div>


                        <button
                            class="channel-action"
                            onclick="editChannel(
                                '${escapeJS(
                        channel.channel_id || ''
                    )}'
                            )"
                        >
                            编辑
                        </button>

                    </div>

                `
            )
            .join('');

}


/* =========================================================
   视频
   ========================================================= */

async function loadVideos() {

    try {

        const videos =
            await apiGet(
                '/videos?limit=20'
            );


        const list =
            Array.isArray(videos)
                ? videos
                : [];


        renderVideos(
            list
        );


        document.getElementById(
            'videoResultCount'
        ).textContent =
            `${list.length} 条视频`;

    } catch (error) {

        console.warn(
            '无法读取视频：',
            error
        );


        document.getElementById(
            'youtubeFeed'
        ).innerHTML = `

            <div class="ai-empty">

                暂时无法读取视频数据。
                请检查 Python 后端是否正在运行。

            </div>

        `;

    }

}


/* =========================================================
   渲染视频
   ========================================================= */

function renderVideos(videos) {

    const feed =
        document.getElementById(
            'youtubeFeed'
        );


    const keyword =
        document.getElementById(
            'channelSearch'
        ).value
            .trim()
            .toLowerCase();


    const filtered =
        videos.filter(
            video => {

                const category =
                    normalizeCategory(
                        video.category
                    );


                const matchesCategory =
                    currentCategory === 'all' ||
                    category === currentCategory;


                const text =
                    (
                        video.title ||
                        ''
                    ) +
                    (
                        video.channel_name ||
                        ''
                    );


                const matchesSearch =
                    !keyword ||
                    text
                        .toLowerCase()
                        .includes(keyword);


                return (
                    matchesCategory &&
                    matchesSearch
                );

            }
        );


    if (!filtered.length) {

        feed.innerHTML = `

            <div class="ai-empty">
                暂无符合条件的视频
            </div>

        `;

        return;

    }


    feed.innerHTML =
        filtered
            .map(
                video => `

                    <article
                        class="youtube-video"
                        onclick="openVideo(
                            '${escapeJS(
                    video.video_id || ''
                )}'
                        )"
                    >

                        <div class="video-thumb">
                            ${video.thumbnail
                        ? `
                                        <img
                                            src="${escapeHTML(
                            video.thumbnail
                        )}"
                                            alt="${escapeHTML(
                            video.title || 'YouTube 视频'
                        )}"
                                            loading="lazy"
                                        >
                                    `
                        : `
                                        <span class="video-thumb-empty">
                                            ▶
                                        </span>
                                    `
                    }
                        </div>


                        <div class="video-info">

                            <div class="video-channel">

                                <span
                                    class="video-channel-dot"
                                ></span>

                                ${escapeHTML(
                        video.channel_name ||
                        'Unknown'
                    )}

                            </div>


                            <h3>

                                ${escapeHTML(
                        video.title ||
                        '未命名视频'
                    )}

                            </h3>


                            <p>

                                ${formatDate(
                        video.published_at
                    )}

                                · YouTube Data API

                            </p>

                        </div>


                        <div class="video-time">

                            ${relativeTime(
                        video.published_at
                    )}

                        </div>


                        <div class="video-arrow">
                            →
                        </div>

                    </article>

                `
            )
            .join('');

}


/* =========================================================
   AI TOP 10
   ========================================================= */

async function loadAIRanking() {

    try {

        const rankings =
            await apiGet(
                '/ai/top?limit=10'
            );


        const list =
            Array.isArray(rankings)
                ? rankings
                : [];


        renderAIRanking(
            list
        );


        document.getElementById(
            'aiRankingTime'
        ).textContent =
            'AI ANALYSIS · LIVE';

    } catch (error) {

        console.warn(
            '无法读取 AI 排名：',
            error
        );


        document.getElementById(
            'aiRanking'
        ).innerHTML = `

            <div class="ai-empty">

                暂无 AI 分析结果。
                等待抓取视频后进行分析。

            </div>

        `;

    }

}


/* =========================================================
   渲染 AI 排名
   ========================================================= */

function renderAIRanking(rankings) {

    const container =
        document.getElementById(
            'aiRanking'
        );


    if (!rankings.length) {

        container.innerHTML = `

            <div class="ai-empty">
                当前暂无 AI 分析结果
            </div>

        `;

        return;

    }


    let html = `

        <div class="ai-ranking-header">

            <div>
                RANK
            </div>

            <div>
                VIDEO / AI ANALYSIS
            </div>

            <div>
                CHANNEL
            </div>

            <div>
                TOPIC
            </div>

            <div>
                SCORE
            </div>

        </div>

    `;


    rankings
        .slice(0, 10)
        .forEach(
            (item, index) => {

                const rank =
                    index + 1;


                html += `

                    <div
                        class="ai-ranking-row"
                    >

                        <div
                            class="
                                ai-rank
                                ${rank <= 3 ? 'top' : ''}
                            "
                        >
                            ${String(
                    rank
                ).padStart(2, '0')}
                        </div>


                        <div
                            class="ai-ranking-title"
                        >

                            <strong>

                                ${escapeHTML(
                    item.title ||
                    '未命名视频'
                )}

                            </strong>


                            <span>

                                ${escapeHTML(
                    item.reason ||
                    item.summary ||
                    'AI 分析中'
                )}

                            </span>

                        </div>


                        <div
                            class="ai-ranking-channel"
                        >

                            ${escapeHTML(
                    item.channel_name ||
                    '—'
                )}

                        </div>


                        <div>

                            <span
                                class="ai-topic"
                            >

                                ${escapeHTML(
                    item.topic ||
                    '综合'
                )}

                            </span>

                        </div>


                        <div class="ai-score">

                            ${formatScore(
                    item.score
                )}

                            <span>
                                / 100
                            </span>

                        </div>

                    </div>

                `;

            }
        );


    container.innerHTML =
        html;

}


/* =========================================================
   立即抓取
   ========================================================= */

async function checkNow() {

    const button =
        document.querySelector(
            '.yt-primary'
        );


    button.disabled = true;

    button.textContent =
        '正在抓取...';


    try {

        const response =
            await fetch(
                API_BASE + '/check',
                {
                    method: 'POST'
                }
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }


        const result =
            await response.json();


        if (result.success === false) {

            throw new Error(
                result.message ||
                '抓取失败'
            );

        }


        button.textContent =
            '✓ 抓取完成';


        await loadAllData();

    } catch (error) {

        console.warn(
            '抓取失败：',
            error
        );


        button.textContent =
            '× 抓取失败';

    }


    setTimeout(
        () => {

            button.disabled = false;

            button.textContent =
                '▶ 立即抓取';

        },
        1500
    );

}


/* =========================================================
   更新配置
   ========================================================= */

async function updateConfig() {

    const enabled =
        document.getElementById(
            'monitorSwitch'
        ).checked;


    const maxResults =
        Number(
            document.getElementById(
                'maxResults'
            ).value
        );


    const uploadOnly =
        document.getElementById(
            'uploadOnlySwitch'
        ).checked;


    const saveDescription =
        document.getElementById(
            'descriptionSwitch'
        ).checked;


    const notificationEnabled =
        document.getElementById(
            'notificationSwitch'
        ).checked;


    try {

        const response =
            await fetch(
                API_BASE + '/config',
                {
                    method: 'PUT',

                    headers: {
                        'Content-Type':
                            'application/json'
                    },

                    body: JSON.stringify({

                        enabled:
                            enabled,

                        max_results:
                            maxResults,

                        upload_only:
                            uploadOnly,

                        save_description:
                            saveDescription,

                        notification_enabled:
                            notificationEnabled

                    })
                }
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }


        await loadConfig();

        await loadStatus();

    } catch (error) {

        console.warn(
            '配置更新失败：',
            error
        );

    }

}


/* =========================================================
   修改检查间隔
   ========================================================= */

async function updateInterval() {

    const select =
        document.getElementById(
            'intervalSelect'
        );


    const seconds =
        Number(
            select.value
        );


    updateIntervalDisplay(
        seconds
    );


    try {

        const response =
            await fetch(
                API_BASE + '/config',
                {
                    method: 'PUT',

                    headers: {
                        'Content-Type':
                            'application/json'
                    },

                    body: JSON.stringify({
                        interval:
                            seconds
                    })
                }
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }


        await loadStatus();

    } catch (error) {

        console.warn(
            '检查间隔更新失败：',
            error
        );

    }

}


/* =========================================================
   检查间隔显示
   ========================================================= */

function updateIntervalDisplay(seconds) {

    let label = '5m';


    if (seconds === 60) {

        label = '1m';

    } else if (seconds === 600) {

        label = '10m';

    } else if (seconds === 1800) {

        label = '30m';

    } else {

        label =
            `${Math.round(
                seconds / 60
            )}m`;

    }


    document.getElementById(
        'intervalValue'
    ).textContent =
        label;

}


/* =========================================================
   加载配置
   ========================================================= */

async function loadConfig() {

    try {

        const data =
            await apiGet('/config');


        if (
            data.enabled !== undefined
        ) {

            document.getElementById(
                'monitorSwitch'
            ).checked =
                Boolean(
                    data.enabled
                );

        }


        if (
            data.interval !== undefined
        ) {

            document.getElementById(
                'intervalSelect'
            ).value =
                String(
                    data.interval
                );


            updateIntervalDisplay(
                Number(
                    data.interval
                )
            );

        }


        if (
            data.max_results !== undefined
        ) {

            document.getElementById(
                'maxResults'
            ).value =
                String(
                    data.max_results
                );

        }


        if (
            data.upload_only !== undefined
        ) {

            document.getElementById(
                'uploadOnlySwitch'
            ).checked =
                Boolean(
                    data.upload_only
                );

        }


        if (
            data.save_description !== undefined
        ) {

            document.getElementById(
                'descriptionSwitch'
            ).checked =
                Boolean(
                    data.save_description
                );

        }


        if (
            data.notification_enabled !==
            undefined
        ) {

            document.getElementById(
                'notificationSwitch'
            ).checked =
                Boolean(
                    data.notification_enabled
                );

        }

    } catch (error) {

        console.warn(
            '无法读取配置：',
            error
        );

    }

}


/* =========================================================
   分类
   ========================================================= */

function selectCategory(
    button,
    category
) {

    document
        .querySelectorAll(
            '.yt-category'
        )
        .forEach(
            item => {

                item.classList.remove(
                    'active'
                );

            }
        );


    button.classList.add(
        'active'
    );


    currentCategory =
        category;


    loadVideos();

}


/* =========================================================
   搜索频道
   ========================================================= */

function filterChannels() {

    const keyword =
        document.getElementById(
            'channelSearch'
        ).value
            .trim()
            .toLowerCase();


    document
        .querySelectorAll(
            '.channel-row:not(.header)'
        )
        .forEach(
            row => {

                const text =
                    row.textContent
                        .toLowerCase();


                row.style.display =
                    !keyword ||
                        text.includes(
                            keyword
                        )
                        ? ''
                        : 'none';

            }
        );


    loadVideos();

}


/* =========================================================
   打开视频
   ========================================================= */

function openVideo(videoId) {

    if (!videoId) {

        return;

    }


    window.open(
        `https://www.youtube.com/watch?v=${encodeURIComponent(
            videoId
        )}`,
        '_blank'
    );

}


/* =========================================================
   添加频道 Dialog
   ========================================================= */

function openChannelDialog() {

    document
        .getElementById(
            'channelDialog'
        )
        .classList.add(
            'show'
        );


    document
        .getElementById(
            'newChannelName'
        )
        .focus();

}


function closeChannelDialog() {

    document
        .getElementById(
            'channelDialog'
        )
        .classList.remove(
            'show'
        );

}


function closeDialogOnBackground(
    event
) {

    if (
        event.target.id ===
        'channelDialog'
    ) {

        closeChannelDialog();

    }

}


/* =========================================================
   保存频道
   ========================================================= */

async function saveChannel() {

    const name =
        document.getElementById(
            'newChannelName'
        ).value.trim();


    const channelId =
        document.getElementById(
            'newChannelId'
        ).value.trim();


    const category =
        document.getElementById(
            'newChannelCategory'
        ).value;


    if (!name) {

        alert(
            '请输入频道名称。'
        );

        return;

    }


    if (!channelId) {

        alert(
            '请输入 YouTube Channel ID。'
        );

        return;

    }


    try {

        const response =
            await fetch(
                API_BASE + '/channels',
                {
                    method: 'POST',

                    headers: {
                        'Content-Type':
                            'application/json'
                    },

                    body:
                        JSON.stringify({

                            name:
                                name,

                            channel_id:
                                channelId,

                            category:
                                category,

                            enabled:
                                true

                        })
                }
            );


        const result =
            await response.json();


        if (
            !response.ok ||
            result.success === false
        ) {

            throw new Error(
                result.message ||
                `HTTP ${response.status}`
            );

        }


        closeChannelDialog();


        document.getElementById(
            'newChannelName'
        ).value = '';


        document.getElementById(
            'newChannelId'
        ).value = '';


        await loadChannels();


        await loadStatus();

    } catch (error) {

        console.warn(
            '添加频道失败：',
            error
        );


        alert(
            error.message ||
            '添加频道失败，请检查后端 API。'
        );

    }

}


/* =========================================================
   编辑频道
   ========================================================= */

function editChannel(channelId) {

    /*
     * 目前保留入口。
     *
     * 后续可以扩展：
     *
     * PUT /api/youtube/channels/{channel_id}
     */

    console.log(
        '编辑频道:',
        channelId
    );

}


/* =========================================================
   API 状态
   ========================================================= */

function updateAPIStatus(status) {

    const metric =
        document.getElementById(
            'apiMetric'
        );


    const card =
        document.getElementById(
            'youtubeApiStatus'
        );


    if (
        status === 'ok' ||
        status === 'active' ||
        status === true
    ) {

        metric.textContent =
            'OK';


        card.textContent =
            'API KEY 已读取';


        card.classList.remove(
            'warning'
        );

    } else {

        metric.textContent =
            'WARN';


        card.textContent =
            'API KEY 未配置';


        card.classList.add(
            'warning'
        );

    }

}


/* =========================================================
   Monitor 状态
   ========================================================= */

function updateMonitorStatus(
    monitoring
) {

    const status =
        document.getElementById(
            'monitorStatus'
        );


    const text =
        document.getElementById(
            'monitorStatusText'
        );


    if (monitoring) {

        status.textContent =
            'MONITORING';


        text.textContent =
            '自动监控正在运行';

    } else {

        status.textContent =
            'PAUSED';


        text.textContent =
            '自动监控已暂停';

    }

}


/* =========================================================
   分类标准化
   ========================================================= */

function normalizeCategory(
    category
) {

    if (!category) {

        return '';

    }


    const value =
        String(category)
            .trim()
            .toLowerCase();


    const aliases = {

        '播客':
            'podcast',

        'ai / 大模型':
            'ai',

        'ai/大模型':
            'ai',

        '半导体':
            'chip',

        '半导体/芯片':
            'chip',

        '科技公司':
            'company',

        '云计算/软件/企业服务':
            'company',

        '汽车':
            'auto',

        '汽车/新能源/自动驾驶':
            'auto',

        '航天':
            'space',

        '航天/商业航天':
            'space',

        '金融':
            'finance',

        '金融/投资机构':
            'finance',

        '财经媒体':
            'media',

        '财经媒体/宏观经济':
            'media'

    };


    return (
        aliases[value] ||
        value
    );

}


/* =========================================================
   分类名称
   ========================================================= */

function categoryLabel(
    category
) {

    const normalized =
        normalizeCategory(
            category
        );


    const labels = {

        podcast:
            '播客',

        ai:
            'AI / 大模型',

        chip:
            '半导体',

        company:
            '科技公司',

        auto:
            '汽车',

        space:
            '航天',

        finance:
            '金融',

        media:
            '财经媒体'

    };


    return (
        labels[normalized] ||
        category ||
        '其他'
    );

}


/* =========================================================
   时间
   ========================================================= */

function relativeTime(
    value
) {

    if (!value) {

        return '—';

    }


    const date =
        new Date(value);


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return '—';

    }


    const diff =
        Math.max(
            0,
            Date.now() -
            date.getTime()
        );


    const minutes =
        Math.floor(
            diff / 60000
        );


    if (minutes < 1) {

        return '刚刚';

    }


    if (minutes < 60) {

        return `${minutes} 分钟前`;

    }


    const hours =
        Math.floor(
            minutes / 60
        );


    if (hours < 24) {

        return `${hours} 小时前`;

    }


    const days =
        Math.floor(
            hours / 24
        );


    return `${days} 天前`;

}


/* =========================================================
   日期
   ========================================================= */

function formatDate(
    value
) {

    if (!value) {

        return '—';

    }


    const date =
        new Date(value);


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return '—';

    }


    return date.toLocaleDateString(
        'zh-CN',
        {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        }
    );

}


/* =========================================================
   时间
   ========================================================= */

function formatTime(
    value
) {

    const date =
        new Date(value);


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return String(value);

    }


    return date.toLocaleTimeString(
        'zh-CN'
    );

}


/* =========================================================
   AI Score
   ========================================================= */

function formatScore(
    score
) {

    const value =
        Number(score);


    if (
        Number.isNaN(value)
    ) {

        return '—';

    }


    return Math.round(
        value
    );

}


/* =========================================================
   HTML 安全
   ========================================================= */

function escapeHTML(
    value
) {

    return String(
        value ?? ''
    )
        .replace(
            /&/g,
            '&amp;'
        )
        .replace(
            /</g,
            '&lt;'
        )
        .replace(
            />/g,
            '&gt;'
        )
        .replace(
            /"/g,
            '&quot;'
        )
        .replace(
            /'/g,
            '&#039;'
        );

}


/* =========================================================
   JavaScript 字符串安全
   ========================================================= */

function escapeJS(
    value
) {

    return String(
        value ?? ''
    )
        .replace(
            /\\/g,
            '\\\\'
        )
        .replace(
            /'/g,
            "\\'"
        )
        .replace(
            /\n/g,
            '\\n'
        )
        .replace(
            /\r/g,
            '\\r'
        );

}