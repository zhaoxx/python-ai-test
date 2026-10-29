CREATE TABLE IF NOT EXISTS `python_ai_chat_memory` (
   `id` bigint NOT NULL AUTO_INCREMENT,
   `conversation_id` varchar(36) NOT NULL,
    `content` longtext NOT NULL,
    `type` varchar(20) NOT NULL,
    `timestamp` timestamp NOT NULL,
    `message_id` varchar(36) NOT NULL DEFAULT '' COMMENT '消息唯一标识',
    PRIMARY KEY (`id`),
    KEY `idx_conversation_id_timestamp` (`conversation_id`,`timestamp`),
    KEY `uk_message_id` (`message_id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;