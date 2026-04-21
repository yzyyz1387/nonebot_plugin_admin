from .menu_registry import menu_registry as _reg


def _register_all() -> None:
    """
    注册all
    :return: None
    """
    _reg.register("基础群管", "禁 @用户 [时长]", "禁言用户，不填时长则随机", permission="管理员", aliases=["禁言"])
    _reg.register("基础群管", "解 @用户", "解除禁言", permission="管理员")
    _reg.register("基础群管", "/全员", '全体禁言/解禁，含"解"字则解禁', permission="管理员", aliases=["/all"])
    _reg.register("基础群管", "改 @用户 名片", "修改群名片", permission="管理员")
    _reg.register("基础群管", "头衔 @用户 头衔", "设置群头衔", permission="所有人")
    _reg.register("基础群管", "删头衔 @用户", "删除群头衔", permission="所有人")
    _reg.register("基础群管", "踢 @用户", "踢出群聊（可重新加群）", permission="管理员")
    _reg.register("基础群管", "黑 @用户", "踢出并拉黑（不可重新加群）", permission="管理员")
    _reg.register("基础群管", "管理员+ @用户", "设置管理员", permission="群主")
    _reg.register("基础群管", "管理员- @用户", "取消管理员", permission="群主")
    _reg.register("基础群管", "加精", "回复消息设为精华", permission="管理员", aliases=["set_essence"])
    _reg.register("基础群管", "取消精华", "取消精华标记", permission="管理员", aliases=["取消加精"])
    _reg.register("基础群管", "撤回 [@用户] [数量]", "撤回消息，回复撤回该条；@用户撤回最近N条", permission="管理员", aliases=["recall"])

    _reg.register("审批管理", "查看词条", "查看本群审批词条", permission="管理员", aliases=["/sp", "/审批"])
    _reg.register("审批管理", "词条+ 词条内容", "添加本群审批词条", permission="管理员", aliases=["/sp+", "词条加"])
    _reg.register("审批管理", "词条- 词条内容", "删除本群审批词条", permission="管理员", aliases=["/sp-", "词条减"])
    _reg.register("审批管理", "词条拒绝 +词条/-词条", "管理审批黑名单", permission="管理员", aliases=["/spx", "拒绝词条"])
    _reg.register("审批管理", "所有词条", "查看所有群审批词条", permission="超管", aliases=["/susp", "/su审批"])
    _reg.register("审批管理", "指定词条+ 群号 词条", "为指定群添加审批词条", permission="超管", aliases=["/susp+"])
    _reg.register("审批管理", "指定词条- 群号 词条", "删除指定群审批词条", permission="超管", aliases=["/susp-"])
    _reg.register("审批管理", "分管", "查看本群分群管理员", permission="管理员", aliases=["/gad"])
    _reg.register("审批管理", "分管+ @用户", "添加分群管理员", permission="管理员", aliases=["分管加"])
    _reg.register("审批管理", "分管- @用户", "移除分群管理员", permission="管理员", aliases=["分管减"])
    _reg.register("审批管理", "接收", "切换超管接收审批通知", permission="超管")
    _reg.register("审批管理", "ai拒绝 开/关", "开关AI自动拒绝广告", permission="管理员")
    _reg.register("审批管理", "ai拒绝prompt 规则", "设置AI审核自定义规则", permission="管理员")
    _reg.register("审批管理", "请求 flag 同意/拒绝", "手动处理入群请求", permission="管理员")

    _reg.register("内容审核", "添加违禁词 词条", "添加违禁词", permission="管理员", aliases=["增加违禁词"])
    _reg.register("内容审核", "删除违禁词 词条", "删除违禁词", permission="管理员", aliases=["移除违禁词"])
    _reg.register("内容审核", "查看违禁词", "查看违禁词列表", permission="管理员", aliases=["违禁词列表"])

    _reg.register("统计分析", "记录本群", "开启本群消息记录", permission="管理员")
    _reg.register("统计分析", "停止记录本群", "停止本群消息记录", permission="管理员")
    _reg.register("统计分析", "今日榜首", "查看今日发言最多的人", permission="所有人", aliases=["今天谁话多"])
    _reg.register("统计分析", "今日发言排行", "查看今日发言排行", permission="所有人", aliases=["今日排行榜"])
    _reg.register("统计分析", "昨日发言排行", "查看昨日发言排行", permission="所有人", aliases=["昨日排行榜"])
    _reg.register("统计分析", "排行", "查看历史总发言排行", permission="所有人", aliases=["排行榜", "谁话多"])
    _reg.register("统计分析", "发言数 @用户", "查询历史总发言数", permission="所有人", aliases=["发言量"])
    _reg.register("统计分析", "今日发言数 @用户", "查询今日发言数", permission="所有人", aliases=["今日发言量"])
    _reg.register("统计分析", "群词云", "生成本群词云图片", permission="所有人", aliases=["词云"])
    _reg.register("统计分析", "添加停用词 词语", "添加词云停用词", permission="管理员", aliases=["增加停用词"])
    _reg.register("统计分析", "删除停用词 词语", "删除词云停用词", permission="管理员", aliases=["移除停用词"])
    _reg.register("统计分析", "停用词列表", "查看停用词", permission="管理员", aliases=["查看停用词"])

    _reg.register("广播", "广播 内容", "向所有群发送广播", permission="超管", aliases=["告诉所有人"])
    _reg.register("广播", "广播排除+/- 群号", "管理广播排除群", permission="超管")
    _reg.register("广播", "排除列表", "查看广播排除群列表", permission="超管")
    _reg.register("广播", "群列表", "查看机器人所在群列表", permission="超管")
    _reg.register("广播", "广播帮助", "查看广播使用帮助", permission="所有人")

    _reg.register("成员清理", "成员清理", "按规则批量清理群成员", permission="群主")
    _reg.register("成员清理", "清理解锁", "清除异常中断的清理锁", permission="群主")

    _reg.register("事件通知", "开关防撤回", "开启/关闭防撤回功能", permission="管理员")
    _reg.register("事件通知", "开关事件通知", "开启/关闭事件通知功能", permission="管理员")

    _reg.register("系统", "开关 功能名", "切换功能开关", permission="管理员")
    _reg.register("系统", "开关状态", "查看本群功能开关状态", permission="管理员")
    _reg.register("系统", "面板地址", "获取Web管理面板地址", permission="超管", aliases=["获取面板"])
    _reg.register("系统", "数据库地址", "获取ORM数据库地址", permission="超管")
    _reg.register("系统", "群管菜单", "显示本菜单", permission="所有人")


_register_all()
