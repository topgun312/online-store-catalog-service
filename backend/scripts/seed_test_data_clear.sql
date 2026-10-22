BEGIN;

DELETE FROM product WHERE id::text LIKE '00000000-%';

DELETE FROM category
WHERE id IN (
    '0b7d9e1a-2c3f-4b5a-9d6e-7f8a9b0c1d2e',
    '1c8e2f3b-4d5a-4c6b-8e7f-9a0b1c2d3e4f',
    '2d9f3a4c-5e6b-4d7c-9f8a-0b1c2d3e4f5a'
);

COMMIT;
