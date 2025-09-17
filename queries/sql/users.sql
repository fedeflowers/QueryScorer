CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO users (username, email) VALUES
('alice', 'alice@example.com'),
('bob', 'bob@example.com'),
('charlie', 'charlie@example.com'),
('david', 'david@example.com'),
('eva', 'eva@example.com'),
('frank', 'frank@example.com'),
('grace', 'grace@example.com'),
('henry', 'henry@example.com'),
('isabel', 'isabel@example.com'),
('jack', 'jack@example.com');
