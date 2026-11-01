"""Editorial categories from the v2 catalog. Labels are translated; facts are not."""

from __future__ import annotations


def slugify(label: str) -> str:
    return label.lower().replace(" & ", "-").replace(" ", "-")


def _cat(label: str, zh: str, blurb_zh: str, blurb_en: str, essay_zh: list[str], essay_en: list[str]) -> dict:
    return {
        "id": slugify(label),
        "en": label,
        "zh": zh,
        "blurb_zh": blurb_zh,
        "blurb_en": blurb_en,
        "essay_zh": essay_zh,
        "essay_en": essay_en,
    }


CATEGORIES: list[dict] = [
    _cat(
        "Official",
        "官方参考",
        "协议组织名下的参考实现。一条记录是一个仓库，不是仓库里的每一台服务器。",
        "Reference implementations under the protocol org. One row is one repository.",
        [
            "这一类来自目录种子里的官方参考仓库。分数和安全评估都落在这一个仓库上，不会自动分给仓库内部的每一台示例服务器。",
            "采用之前打开仓库，看你要的是哪一台服务器、它读哪些环境变量。公开安全评估只告诉你许可证是否被识别、最近有没有推送，以及 README 摘录里有没有弃用声明。",
        ],
        [
            "This category is the official reference repository kept from the seed list. The score and the security assessment apply to that one repository, not to each sample server inside it.",
            "Before you adopt one, open the repo and see which server you actually want and which environment variables it reads. The public security assessment only tells you whether a license id was recognized, whether the repo was pushed recently, and whether the README excerpt contains a deprecation notice.",
        ],
    ),
    _cat(
        "Dev Tools",
        "开发工具",
        "种子列表里单独标出的开发工具仓库。",
        "The developer-tool repository kept as its own category from the seed list.",
        [
            "这一类目前是种子数据里单独标成 Dev Tools 的仓库，和后面按关键词归入「编程与开发」的仓库不是同一次归类。页面上的 GitHub 描述仍是原文。",
            "把它接到代理之前，先看它要求哪种令牌。安全评估不会把星标换成「可以放心授权」的结论。",
        ],
        [
            "This category is the seed entry labeled Dev Tools. It is not the same bucket as Coding & Dev, which comes from the keyword rules. The GitHub description on the page is still the original text.",
            "Before you connect it to an agent, read which token it asks for. The security assessment does not turn a star count into permission to grant that token.",
        ],
    ),
    _cat(
        "Browser",
        "浏览器",
        "种子列表里单独标出的浏览器仓库。",
        "The browser repository kept as its own category from the seed list.",
        [
            "这一类是种子数据里的浏览器条目，和「浏览器与网页」分开，因为两边的分类来源不同。描述以 GitHub 原文为准。",
            "浏览器工具可能碰到已经登录的配置文件。安全评估不衡量它是否隔离 cookie。那要读 README，而不是读星标。",
        ],
        [
            "This is the seed browser entry. It stays separate from Browser & Web because the two labels come from different steps in the catalog. The description is the GitHub text.",
            "A browser tool can meet a profile that is already signed in. The security assessment does not measure cookie isolation. That is in the README, not in the star count.",
        ],
    ),
    _cat(
        "Browser & Web",
        "浏览器与网页",
        "名称、描述或话题命中浏览器、爬取或网页相关词的仓库。",
        "Repositories whose name, description, or topics matched browser, crawl, or web terms.",
        [
            "分类是对仓库名、GitHub 描述和话题做的关键词归类，不是人工逐一试用。所以这里会同时出现浏览器自动化、爬虫和带 web 话题的项目。每条记录下面的描述是 GitHub 原文，用来核对它到底做什么。",
            "这一类常见的访问面是网页内容和浏览器会话。公开安全评估只报告许可证、推送新旧，以及 README 摘录里有没有弃用或警告块。它不证明抓取行为合法，也不证明浏览器上下文是干净的。",
        ],
        [
            "The category is a keyword match on the repository name, GitHub description, and topics, not a hands-on trial. Browser automation, crawlers, and repos tagged web can share this page. The description under each row is the GitHub text, so you can check what it actually claims to do.",
            "The usual access here is page content and browser sessions. The public security assessment reports the license, how recent the push is, and whether the README excerpt contains a deprecation or a warning block. It does not say the crawl is lawful, and it does not say the browser context is clean.",
        ],
    ),
    _cat(
        "Coding & Dev",
        "编程与开发",
        "关键词命中代码、Git、IDE、调试或 SDK 的仓库。",
        "Repositories matched to code, git, IDE, debug, or SDK terms.",
        [
            "这是目录里最大的一类，因为关键词规则把 code、git、ide、sdk 都收了进来。有的是 MCP 服务器，有的是编程代理或带 mcp 话题的开发项目。不要把分类名当成「已确认的 MCP 服务器」这句结论。看该行的 GitHub 描述。",
            "开发工具经常能读仓库和执行命令。安全评估里的维护时间只说明默认分支最近有没有推送，不能区分那次推送是发版还是改了一行文档。",
        ],
        [
            "This is the largest category because the keyword rule collects code, git, ide, and sdk. Some rows are MCP servers, some are coding agents, and some are development projects that carry an mcp topic. The category name is not a finding that every row is a confirmed MCP server. Read the GitHub description on the row.",
            "Developer tools often read repositories and run commands. Maintenance time in the security assessment only says whether the default branch was pushed recently. It does not separate a release from a documentation edit.",
        ],
    ),
    _cat(
        "Security",
        "安全工具",
        "关键词命中安全、渗透或逆向的仓库。",
        "Repositories matched to security, pentest, or reverse-engineering terms.",
        [
            "这里的「安全」是关键词分类：secur、pentest、reverse、ida、ghidra。它不是本站给这些仓库做的安全认证。本站的安全评估对每一类都一样，只使用许可证、推送时间和 README 词面。",
            "逆向和渗透工具会碰到二进制、调试器和目标系统。收录它们是因为它们出现在公开搜索结果里，不是因为建议拿去攻击没有授权的系统。",
        ],
        [
            "Security here is the keyword bucket: secur, pentest, reverse, ida, ghidra. It is not a certification this site issued. The security assessment is the same shape on every category: license, push time, and README wording.",
            "Reverse-engineering and pentest tools touch binaries, debuggers, and target systems. They are listed because they showed up in the public search, not as a suggestion to attack a system you are not allowed to test.",
        ],
    ),
    _cat(
        "Data & DB",
        "数据与数据库",
        "关键词命中数据库或数据存储的仓库。",
        "Repositories matched to database and data-store terms.",
        [
            "关键词会把 SQL、Postgres、Mongo、Redis、Supabase 以及带 data 的仓库放在一起。描述原文会告诉你它是驱动、服务器还是别的数据工具。",
            "连接串是凭证。安全评估不会写「默认只读」，除非这句话出现在下面引用的 README 里。没有写，就当未知。",
        ],
        [
            "The keywords place SQL, Postgres, Mongo, Redis, Supabase, and repos that say data on one page. The original description tells you whether the project is a driver, a server, or another data tool.",
            "A connection string is a credential. The security assessment does not say the tool defaults to read-only unless that sentence is in the README excerpt below. If it is absent, treat it as unknown.",
        ],
    ),
    _cat(
        "Cloud & Infra",
        "云与基础设施",
        "关键词命中云、容器或基础设施的仓库。",
        "Repositories matched to cloud, container, or infrastructure terms.",
        [
            "AWS、Kubernetes、Docker、Terraform 这类词会进到这里。一个仓库如果是一组服务器的合集，分数仍然只有仓库这一个，不会按云产品拆开。",
            "云上的 MCP 或代理往往是控制面。评估里的许可证和推送时间不代替你自己写的 IAM 或 RBAC。",
        ],
        [
            "Terms such as AWS, Kubernetes, Docker, and Terraform land here. If a repository is a bundle of servers, there is still one score for the repository. It is not split per cloud product.",
            "A cloud MCP or agent is often a control plane. License and push time in the assessment do not replace the IAM or RBAC you attach.",
        ],
    ),
    _cat(
        "Docs & Knowledge",
        "文档与知识",
        "关键词命中文档、记忆、检索或笔记的仓库。",
        "Repositories matched to docs, memory, retrieval, or notes.",
        [
            "文档、RAG、记忆、Notion、Obsidian、搜索这些词归在这里。有的项目提供的是上下文，有的是笔记软件，有的只是在话题里写了 mcp。以描述原文区分。",
            "知识库工具会复制你的文档。安全评估不说明索引存在哪里、谁能查询。这些如果没写在摘录里，就还是未知。",
        ],
        [
            "Docs, RAG, memory, Notion, Obsidian, and search terms are grouped here. Some projects supply context, some are note apps, and some only carry mcp in a topic. Use the original description to tell them apart.",
            "A knowledge tool copies your documents. The security assessment does not say where the index lives or who can query it. If the excerpt does not say, it is still unknown.",
        ],
    ),
    _cat(
        "Design & Media",
        "设计与媒体",
        "关键词命中设计、图像、音视频的仓库。",
        "Repositories matched to design, image, audio, or video terms.",
        [
            "Figma、绘图、图像、音视频、Blender 这些词会进到这里。名字像官方，不代表仓库描述承认自己是官方。描述里如果写了社区或非从属，以那句原文为准。",
            "编辑器桥通常能看见当前打开的文件。安全评估不另做「是否会改文件」的测试。",
        ],
        [
            "Figma, drawing, image, audio, video, and Blender terms land here. A name that sounds official does not mean the repository description claims to be official. If the description says community or unaffiliated, that sentence is the one to trust.",
            "An editor bridge can usually see the file that is open. The security assessment does not add a test of whether it can edit the file.",
        ],
    ),
    _cat(
        "Marketing & Social",
        "营销与社交",
        "关键词命中营销、广告或社交平台的仓库。",
        "Repositories matched to marketing, ads, or social platforms.",
        [
            "SEO、广告和社交平台相关的词归在这里，包括描述或话题里出现具体站点名字的项目。描述原文是项目自己的介绍，本站不改写成推荐语。",
            "社交数据往往是别人的内容。安全评估不判断采集是否符合平台条款。",
        ],
        [
            "SEO, ads, and social-platform terms are grouped here, including projects whose description or topics name a specific site. The original description is the project's own summary. This site does not rewrite it as an endorsement.",
            "Social data is often someone else's content. The security assessment does not judge whether collection fits a platform's terms.",
        ],
    ),
    _cat(
        "Mobile & Devices",
        "移动与设备",
        "关键词命中移动端或设备的仓库。",
        "Repositories matched to mobile or device terms.",
        [
            "Android、iOS、mobile、ESP32 这些词会进到这里。有的是设备固件的后端，有的是移动构建工具。看描述，不要只看分类。",
            "设备控制面和手机权限不是星标能说明的。评估页只重复公开仓库上的许可证和维护信号。",
        ],
        [
            "Android, iOS, mobile, and ESP32 terms land here. Some rows are backends for device firmware, some are mobile build tools. Read the description, not only the category.",
            "A device control plane and a phone permission are not something a star count explains. The assessment repeats the license and maintenance signals that are public on the repository.",
        ],
    ),
    _cat(
        "Other",
        "其他",
        "没有命中前面关键词、但仍在收录名单里的仓库。",
        "Repositories in the catalog that matched none of the keyword rules.",
        [
            "没有命中既定关键词的仓库会留在其他。它们仍然来自同一份公开搜索名单：带 mcp 话题或名称、有可识别的 SPDX 许可证、搜索时未归档。未命中关键词不等于来历不明，只是规则没给它一个更窄的类。",
            "读这一类时更要看 GitHub 描述。分类名「其他」不提供功能说明，本站也不会为了填满这一栏编一个功能。",
        ],
        [
            "Repositories that miss the keyword rules stay in Other. They still come from the same public search list: an mcp topic or name, a recognized SPDX license, and not archived at search time. Missing a keyword does not mean the origin is unknown. The rule simply did not assign a narrower bucket.",
            "Read the GitHub description especially carefully here. The label Other does not describe a feature, and this site will not invent one to fill the column.",
        ],
    ),
]


def category_by_id(category_id: str) -> dict:
    for category in CATEGORIES:
        if category["id"] == category_id:
            return category
    raise KeyError(category_id)
