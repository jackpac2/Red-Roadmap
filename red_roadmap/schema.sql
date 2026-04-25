CREATE TABLE IF NOT EXISTS tasks (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  priority ENUM('LOW','MEDIUM','HIGH') DEFAULT 'MEDIUM',
  mode ENUM('AT_PC','AWAY','FLEXIBLE') DEFAULT 'FLEXIBLE',
  status ENUM('PENDING','ACTIVE','AWAY','COMPLETED') DEFAULT 'PENDING',
  reminder_at DATETIME NULL,
  next_check_at DATETIME NULL,
  last_progress_at DATETIME NULL,
  snooze_count INT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME NULL
);

CREATE TABLE IF NOT EXISTS micro_actions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  task_id INT NOT NULL,
  title VARCHAR(255) NOT NULL,
  completed BOOLEAN DEFAULT FALSE,
  completed_at DATETIME NULL,
  sort_order INT DEFAULT 0,
  CONSTRAINT fk_micro_actions_task
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

INSERT INTO tasks (title, priority, mode, status, reminder_at)
VALUES
('Write project draft', 'HIGH', 'AT_PC', 'PENDING', DATE_ADD(NOW(), INTERVAL 3 MINUTE)),
('Walk and think about architecture', 'MEDIUM', 'AWAY', 'PENDING', DATE_ADD(NOW(), INTERVAL 10 MINUTE)),
('Inbox cleanup', 'LOW', 'FLEXIBLE', 'PENDING', NULL);

INSERT INTO micro_actions (task_id, title, completed, sort_order)
SELECT id, 'Open editor', FALSE, 0 FROM tasks WHERE title = 'Write project draft';

INSERT INTO micro_actions (task_id, title, completed, sort_order)
SELECT id, 'Write first paragraph', FALSE, 1 FROM tasks WHERE title = 'Write project draft';

INSERT INTO micro_actions (task_id, title, completed, sort_order)
SELECT id, 'Set a 15-minute timer', FALSE, 0 FROM tasks WHERE title = 'Walk and think about architecture';
