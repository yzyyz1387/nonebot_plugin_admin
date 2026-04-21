from __future__ import annotations

ORM_MODELS_AVAILABLE = False
ORM_IMPORT_ERROR: Exception | None = None

try:
    from nonebot_plugin_tortoise_orm import add_model
    from tortoise import fields
    from tortoise.models import Model
except Exception as err:
    ORM_IMPORT_ERROR = err
    add_model = None
    fields = None

    class Model:  # type: ignore[no-redef]
        pass
else:
    add_model(__name__)
    ORM_MODELS_AVAILABLE = True


if ORM_MODELS_AVAILABLE:
    class StatisticsGroupRecordSetting(Model):
        id = fields.IntField(pk=True)
        group_id = fields.CharField(max_length=32, unique=True)
        enabled = fields.BooleanField(default=False)
        updated_at = fields.DatetimeField(auto_now=True)

        class Meta:
            table = "admin_statistics_group_record_setting"


    class StatisticsGroupStopWord(Model):
        id = fields.IntField(pk=True)
        group_id = fields.CharField(max_length=32)
        word = fields.CharField(max_length=255)
        created_at = fields.DatetimeField(auto_now_add=True)

        class Meta:
            table = "admin_statistics_group_stop_word"
            unique_together = (("group_id", "word"),)
            indexes = (("group_id",),)


    class StatisticsWordCorpus(Model):
        id = fields.IntField(pk=True)
        group_id = fields.CharField(max_length=32)
        content = fields.TextField()
        source_type = fields.CharField(max_length=32, default="message")
        created_at = fields.DatetimeField(auto_now_add=True)

        class Meta:
            table = "admin_statistics_word_corpus"
            indexes = (("group_id",), ("group_id", "created_at"))


    class StatisticsDailyMessageStat(Model):
        id = fields.IntField(pk=True)
        group_id = fields.CharField(max_length=32)
        user_id = fields.CharField(max_length=32)
        stat_date = fields.DateField()
        message_count = fields.IntField(default=0)
        updated_at = fields.DatetimeField(auto_now=True)

        class Meta:
            table = "admin_statistics_daily_message_stat"
            unique_together = (("group_id", "user_id", "stat_date"),)
            indexes = (("group_id", "stat_date"), ("group_id", "user_id"))


    class StatisticsHistoryMessageStat(Model):
        id = fields.IntField(pk=True)
        group_id = fields.CharField(max_length=32)
        user_id = fields.CharField(max_length=32)
        message_count = fields.IntField(default=0)
        updated_at = fields.DatetimeField(auto_now=True)

        class Meta:
            table = "admin_statistics_history_message_stat"
            unique_together = (("group_id", "user_id"),)
            indexes = (("group_id",), ("group_id", "user_id"))


    class StatisticsMessageRecord(Model):
        id = fields.IntField(pk=True)
        group_id = fields.CharField(max_length=32)
        user_id = fields.CharField(max_length=32)
        message_id = fields.CharField(max_length=64, null=True)
        message_key = fields.CharField(max_length=96, null=True, unique=True)
        plain_text = fields.TextField()
        message_length = fields.IntField(default=0)
        message_date = fields.DateField()
        message_hour = fields.SmallIntField(default=0)
        created_at = fields.DatetimeField()

        class Meta:
            table = "admin_statistics_message_record"
            indexes = (
                ("group_id", "message_date"),
                ("group_id", "user_id", "message_date"),
                ("group_id", "created_at"),
            )

    class RecallMessageArchive(Model):
        id = fields.IntField(pk=True)
        group_id = fields.CharField(max_length=32)
        user_id = fields.CharField(max_length=32)
        message_id = fields.CharField(max_length=64)
        message_key = fields.CharField(max_length=96, unique=True)
        plain_text = fields.TextField(default="")
        payload_json = fields.TextField(default="{}")
        sent_at = fields.DatetimeField()
        created_at = fields.DatetimeField(auto_now_add=True)

        class Meta:
            table = "admin_recall_message_archive"
            indexes = (
                ("group_id", "sent_at"),
                ("group_id", "user_id"),
                ("group_id", "message_id"),
            )

    class DashboardOplogRecord(Model):
        id = fields.IntField(pk=True)
        action = fields.CharField(max_length=32)
        action_label = fields.CharField(max_length=64)
        level = fields.CharField(max_length=16, default="INFO")
        group_id = fields.CharField(max_length=32, null=True)
        user_id = fields.CharField(max_length=32, null=True)
        detail = fields.TextField(default="")
        message = fields.TextField(default="")
        extra_json = fields.TextField(default="{}", null=True)
        created_at = fields.DatetimeField(auto_now_add=True)

        class Meta:
            table = "admin_dashboard_oplog_record"
            indexes = (
                ("group_id",),
                ("action",),
                ("created_at",),
            )

    class MigrationManifest(Model):
        id = fields.IntField(pk=True)
        file_path = fields.CharField(max_length=512, unique=True)
        file_md5 = fields.CharField(max_length=32)
        version = fields.IntField(default=1)
        created_at = fields.DatetimeField(auto_now_add=True)
        updated_at = fields.DatetimeField(auto_now=True)

        class Meta:
            table = "admin_migration_manifest"
            indexes = (("file_path",),)

    class GroupFeatureSwitch(Model):
        id = fields.IntField(pk=True)
        group_id = fields.CharField(max_length=32)
        func_name = fields.CharField(max_length=64)
        enabled = fields.BooleanField(default=False)
        updated_at = fields.DatetimeField(auto_now=True)

        class Meta:
            table = "admin_group_feature_switch"
            unique_together = (("group_id", "func_name"),)
            indexes = (("group_id",),)

    class ApprovalTerm(Model):
        id = fields.IntField(pk=True)
        group_id = fields.CharField(max_length=32)
        term = fields.CharField(max_length=512)
        created_at = fields.DatetimeField(auto_now_add=True)

        class Meta:
            table = "admin_approval_term"
            unique_together = (("group_id", "term"),)
            indexes = (("group_id",),)

    class DeputyAdmin(Model):
        id = fields.IntField(pk=True)
        group_id = fields.CharField(max_length=32)
        user_id = fields.CharField(max_length=32)
        created_at = fields.DatetimeField(auto_now_add=True)

        class Meta:
            table = "admin_deputy_admin"
            unique_together = (("group_id", "user_id"),)
            indexes = (("group_id",),)

    class GlobalConfig(Model):
        id = fields.IntField(pk=True)
        key = fields.CharField(max_length=128, unique=True)
        value = fields.CharField(max_length=512)
        updated_at = fields.DatetimeField(auto_now=True)

        class Meta:
            table = "admin_global_config"
            indexes = (("key",),)

    class ApprovalBlacklistTerm(Model):
        id = fields.IntField(pk=True)
        group_id = fields.CharField(max_length=32)
        term = fields.CharField(max_length=512)
        created_at = fields.DatetimeField(auto_now_add=True)

        class Meta:
            table = "admin_approval_blacklist_term"
            unique_together = (("group_id", "term"),)
            indexes = (("group_id",),)

    class ContentGuardRule(Model):
        id = fields.IntField(pk=True)
        pattern = fields.TextField()
        options = fields.TextField(default="")
        order_index = fields.IntField(default=0)
        enabled = fields.BooleanField(default=True)
        created_at = fields.DatetimeField(auto_now_add=True)

        class Meta:
            table = "admin_content_guard_rule"
            unique_together = (("pattern", "options"),)
            indexes = (("enabled", "order_index"),)

    class AIVerifyConfig(Model):
        id = fields.IntField(pk=True)
        group_id = fields.CharField(max_length=32, unique=True)
        enabled = fields.BooleanField(default=False)
        prompt = fields.TextField(default="")
        updated_at = fields.DatetimeField(auto_now=True)

        class Meta:
            table = "admin_ai_verify_config"
            indexes = (("group_id",),)

    class BroadcastExclusion(Model):
        id = fields.IntField(pk=True)
        user_id = fields.CharField(max_length=32)
        group_id = fields.CharField(max_length=32)
        created_at = fields.DatetimeField(auto_now_add=True)

        class Meta:
            table = "admin_broadcast_exclusion"
            unique_together = (("user_id", "group_id"),)
            indexes = (("user_id",),)

    class UserViolation(Model):
        id = fields.IntField(pk=True)
        group_id = fields.CharField(max_length=32)
        user_id = fields.CharField(max_length=32)
        level = fields.IntField(default=0)
        updated_at = fields.DatetimeField(auto_now=True)

        class Meta:
            table = "admin_user_violation"
            unique_together = (("group_id", "user_id"),)
            indexes = (("group_id",),)

    class ViolationRecord(Model):
        id = fields.IntField(pk=True)
        group_id = fields.CharField(max_length=32)
        user_id = fields.CharField(max_length=32)
        timestamp = fields.CharField(max_length=32)
        label = fields.CharField(max_length=64)
        content = fields.TextField(default="")
        created_at = fields.DatetimeField(auto_now_add=True)

        class Meta:
            table = "admin_violation_record"
            indexes = (("group_id", "user_id"),)
else:
    StatisticsGroupRecordSetting = None
    StatisticsGroupStopWord = None
    StatisticsWordCorpus = None
    StatisticsDailyMessageStat = None
    StatisticsHistoryMessageStat = None
    StatisticsMessageRecord = None
    RecallMessageArchive = None
    DashboardOplogRecord = None
    MigrationManifest = None
    GroupFeatureSwitch = None
    ApprovalTerm = None
    DeputyAdmin = None
    GlobalConfig = None
    ApprovalBlacklistTerm = None
    ContentGuardRule = None
    AIVerifyConfig = None
    BroadcastExclusion = None
    UserViolation = None
    ViolationRecord = None
