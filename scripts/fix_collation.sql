-- 修复数据库 collation 不一致问题
-- 问题：MySQL 8.0 默认 collation 为 utf8mb4_0900_ai_ci，
--       而数据库设定为 utf8mb4_unicode_ci，导致 JOIN 时 collation 冲突
-- 执行方式：Get-Content scripts/fix_collation.sql | mysql -uroot -p stock_sentiment

USE stock_sentiment;

-- 1. 禁用外键检查（避免转换时外键引用列 collation 不一致报错）
SET FOREIGN_KEY_CHECKS = 0;

-- 2. 统一数据库级别 collation
ALTER DATABASE stock_sentiment CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 3. 统一所有表的 collation（按依赖顺序：先父表后子表）
ALTER TABLE stocks CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE users CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE comments CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE sentiments CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE emotions CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE quotes CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE experiment_results CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE aspect_sentiments CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE alerts CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 4. 重新启用外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- 5. 验证修复结果
SELECT TABLE_NAME, TABLE_COLLATION
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'stock_sentiment'
ORDER BY TABLE_NAME;

SELECT 'Collation fix completed successfully!' AS message;
