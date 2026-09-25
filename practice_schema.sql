-- PrepTrack — Practice / judge feature
-- Run this against your existing database:
--   mysql -u root -p preptrack < practice_schema.sql

USE preptrack;

CREATE TABLE IF NOT EXISTS practice_problems (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    difficulty ENUM('Easy', 'Medium', 'Hard') NOT NULL DEFAULT 'Easy',
    topic VARCHAR(100),
    company_id INT,
    statement TEXT NOT NULL,
    starter_code TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS practice_test_cases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    problem_id INT NOT NULL,
    input TEXT NOT NULL,
    expected_output TEXT NOT NULL,
    is_sample BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (problem_id) REFERENCES practice_problems(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS submissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    problem_id INT NOT NULL,
    code MEDIUMTEXT NOT NULL,
    status ENUM('Accepted', 'Wrong Answer', 'Runtime Error', 'Time Limit Exceeded') NOT NULL,
    passed_count INT NOT NULL DEFAULT 0,
    total_count INT NOT NULL DEFAULT 0,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (problem_id) REFERENCES practice_problems(id) ON DELETE CASCADE
);

CREATE INDEX idx_submissions_user_problem ON submissions(user_id, problem_id);

-- ---------------------------------------------------------------------
-- Seed: 5 practice problems across companies, stdin/stdout judged
-- ---------------------------------------------------------------------

INSERT INTO practice_problems (title, slug, difficulty, topic, company_id, statement, starter_code)
SELECT * FROM (SELECT
    'Two Sum (Sorted Input)' AS title,
    'two-sum-sorted' AS slug,
    'Easy' AS difficulty,
    'Arrays' AS topic,
    (SELECT id FROM companies WHERE name='Infosys') AS company_id,
    'You are given a sorted list of integers and a target sum, on two lines of input.\nLine 1: space-separated integers.\nLine 2: the target integer.\n\nPrint the two integers (in the order they appear) that add up to the target, space-separated. Assume exactly one solution exists.\n\nExample input:\n2 7 11 15\n9\n\nExample output:\n2 7' AS statement,
    'nums = list(map(int, input().split()))\ntarget = int(input())\n\n# write your solution below\nfor i in range(len(nums)):\n    for j in range(i + 1, len(nums)):\n        if nums[i] + nums[j] == target:\n            print(nums[i], nums[j])\n            exit()\n' AS starter_code
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM practice_problems WHERE slug = 'two-sum-sorted');

INSERT INTO practice_problems (title, slug, difficulty, topic, company_id, statement, starter_code)
SELECT * FROM (SELECT
    'Reverse a String',
    'reverse-string',
    'Easy',
    'Strings',
    (SELECT id FROM companies WHERE name='TCS'),
    'Read a single line of text and print it reversed.\n\nExample input:\nhello\n\nExample output:\nolleh',
    's = input()\n\n# write your solution below\nprint(s[::-1])\n'
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM practice_problems WHERE slug = 'reverse-string');

INSERT INTO practice_problems (title, slug, difficulty, topic, company_id, statement, starter_code)
SELECT * FROM (SELECT
    'Check Palindrome',
    'check-palindrome',
    'Easy',
    'Strings',
    (SELECT id FROM companies WHERE name='TCS'),
    'Read a single line of text. Print "YES" if it is a palindrome (ignoring case), else print "NO".\n\nExample input:\nMadam\n\nExample output:\nYES',
    's = input().strip().lower()\n\n# write your solution below\nif s == s[::-1]:\n    print("YES")\nelse:\n    print("NO")\n'
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM practice_problems WHERE slug = 'check-palindrome');

INSERT INTO practice_problems (title, slug, difficulty, topic, company_id, statement, starter_code)
SELECT * FROM (SELECT
    'Nth Fibonacci Number',
    'nth-fibonacci',
    'Medium',
    'DP',
    (SELECT id FROM companies WHERE name='Infosys'),
    'Read an integer n. Print the nth Fibonacci number (0-indexed: fib(0)=0, fib(1)=1).\n\nExample input:\n6\n\nExample output:\n8',
    'n = int(input())\n\n# write your solution below\na, b = 0, 1\nfor _ in range(n):\n    a, b = b, a + b\nprint(a)\n'
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM practice_problems WHERE slug = 'nth-fibonacci');

INSERT INTO practice_problems (title, slug, difficulty, topic, company_id, statement, starter_code)
SELECT * FROM (SELECT
    'Count Vowels',
    'count-vowels',
    'Easy',
    'Strings',
    (SELECT id FROM companies WHERE name='Atidan'),
    'Read a single line of text. Print the number of vowels (a, e, i, o, u — case-insensitive) it contains.\n\nExample input:\nHello World\n\nExample output:\n3',
    's = input().lower()\n\n# write your solution below\ncount = sum(1 for ch in s if ch in "aeiou")\nprint(count)\n'
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM practice_problems WHERE slug = 'count-vowels');

-- Test cases (only inserted if the problem was just created above and has no cases yet)

INSERT INTO practice_test_cases (problem_id, input, expected_output, is_sample)
SELECT p.id, t.input, t.expected_output, t.is_sample FROM practice_problems p
JOIN (
    SELECT 'two-sum-sorted' AS slug, '2 7 11 15' AS input, '2 7' AS expected_output, TRUE AS is_sample
    UNION ALL SELECT 'two-sum-sorted', '1 3 4 6 10', '10', TRUE
    UNION ALL SELECT 'two-sum-sorted', '3 2 4', '2 4', FALSE
    UNION ALL SELECT 'two-sum-sorted', '5 75 25', '5 75', FALSE
) t ON t.slug = p.slug
WHERE NOT EXISTS (SELECT 1 FROM practice_test_cases WHERE problem_id = p.id);

INSERT INTO practice_test_cases (problem_id, input, expected_output, is_sample)
SELECT p.id, t.input, t.expected_output, t.is_sample FROM practice_problems p
JOIN (
    SELECT 'reverse-string' AS slug, 'hello' AS input, 'olleh' AS expected_output, TRUE AS is_sample
    UNION ALL SELECT 'reverse-string', 'PrepTrack', 'kcarTperP', TRUE
    UNION ALL SELECT 'reverse-string', 'a', 'a', FALSE
    UNION ALL SELECT 'reverse-string', 'campus placement', 'tnemecalp supmac', FALSE
) t ON t.slug = p.slug
WHERE NOT EXISTS (SELECT 1 FROM practice_test_cases WHERE problem_id = p.id);

INSERT INTO practice_test_cases (problem_id, input, expected_output, is_sample)
SELECT p.id, t.input, t.expected_output, t.is_sample FROM practice_problems p
JOIN (
    SELECT 'check-palindrome' AS slug, 'Madam' AS input, 'YES' AS expected_output, TRUE AS is_sample
    UNION ALL SELECT 'check-palindrome', 'hello', 'NO', TRUE
    UNION ALL SELECT 'check-palindrome', 'racecar', 'YES', FALSE
    UNION ALL SELECT 'check-palindrome', 'TCS', 'NO', FALSE
) t ON t.slug = p.slug
WHERE NOT EXISTS (SELECT 1 FROM practice_test_cases WHERE problem_id = p.id);

INSERT INTO practice_test_cases (problem_id, input, expected_output, is_sample)
SELECT p.id, t.input, t.expected_output, t.is_sample FROM practice_problems p
JOIN (
    SELECT 'nth-fibonacci' AS slug, '6' AS input, '8' AS expected_output, TRUE AS is_sample
    UNION ALL SELECT 'nth-fibonacci', '0', '0', TRUE
    UNION ALL SELECT 'nth-fibonacci', '1', '1', FALSE
    UNION ALL SELECT 'nth-fibonacci', '10', '55', FALSE
) t ON t.slug = p.slug
WHERE NOT EXISTS (SELECT 1 FROM practice_test_cases WHERE problem_id = p.id);

INSERT INTO practice_test_cases (problem_id, input, expected_output, is_sample)
SELECT p.id, t.input, t.expected_output, t.is_sample FROM practice_problems p
JOIN (
    SELECT 'count-vowels' AS slug, 'Hello World' AS input, '3' AS expected_output, TRUE AS is_sample
    UNION ALL SELECT 'count-vowels', 'PrepTrack', '2', TRUE
    UNION ALL SELECT 'count-vowels', 'xyz', '0', FALSE
    UNION ALL SELECT 'count-vowels', 'AEIOU aeiou', '10', FALSE
) t ON t.slug = p.slug
WHERE NOT EXISTS (SELECT 1 FROM practice_test_cases WHERE problem_id = p.id);
