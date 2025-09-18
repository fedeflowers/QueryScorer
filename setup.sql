-- Database setup script with sample data
CREATE TABLE IF NOT EXISTS public.users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100),
  email VARCHAR(100)
);


-- Insert 10 test users
INSERT INTO public.users (name, email) VALUES 
  ('John Doe', 'john@example.com'),
  ('Jane Smith', 'jane@example.com'),
  ('Michael Johnson', 'michael@example.com'),
  ('Emily Brown', 'emily@example.com'),
  ('David Wilson', 'david@example.com'),
  ('Sarah Davis', 'sarah@example.com'),
  ('Robert Miller', 'robert@example.com'),
  ('Lisa Anderson', 'lisa@example.com'),
  ('James Taylor', 'james@example.com'),
  ('Maria Garcia', 'maria@example.com');