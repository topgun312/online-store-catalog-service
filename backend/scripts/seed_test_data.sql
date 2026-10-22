BEGIN;

INSERT INTO category (id, name, slug) VALUES
    ('0b7d9e1a-2c3f-4b5a-9d6e-7f8a9b0c1d2e', 'Электроника', 'electronics'),
    ('1c8e2f3b-4d5a-4c6b-8e7f-9a0b1c2d3e4f', 'Одежда', 'clothing'),
    ('2d9f3a4c-5e6b-4d7c-9f8a-0b1c2d3e4f5a', 'Другое', 'other')
ON CONFLICT (id) DO NOTHING;

INSERT INTO product (
    id,
    title,
    image_key,
    image_content_type,
    image_size_bytes,
    category_id,
    created_at,
    updated_at
)
SELECT
    ('00000000-0000-4000-8000-' || lpad(i::text, 12, '0'))::uuid,
    t.names[((i - 1) % 24) + 1] || ' «Модель ' || i || '»',
    'products/test/seed-' || lpad(i::text, 4, '0') || '.jpg',
    'image/jpeg',
    512 * 1024,
    t.cats[((i - 1) % 24) + 1],
    TIMEZONE('utc', now()) - make_interval(hours => i),
    TIMEZONE('utc', now()) - make_interval(hours => i)
FROM generate_series(1, 20) AS i
CROSS JOIN LATERAL (
    SELECT
        ARRAY[
            'Смартфон', 'Ноутбук', 'Наушники', 'Планшет',
            'Умная лампа', 'Робот-пылесос', 'Монитор', 'Игровая клавиатура',
            'Футболка', 'Куртка', 'Джинсы', 'Свитшот',
            'Кепка', 'Шарф', 'Худи', 'Носки',
            'Кружка', 'Рюкзак', 'Зонт', 'Полотенце',
            'Ежедневник', 'Ручка', 'Органайзер', 'Бутылка для воды'
        ] AS names,
        ARRAY[
            '0b7d9e1a-2c3f-4b5a-9d6e-7f8a9b0c1d2e', '0b7d9e1a-2c3f-4b5a-9d6e-7f8a9b0c1d2e',
            '0b7d9e1a-2c3f-4b5a-9d6e-7f8a9b0c1d2e', '0b7d9e1a-2c3f-4b5a-9d6e-7f8a9b0c1d2e',
            '0b7d9e1a-2c3f-4b5a-9d6e-7f8a9b0c1d2e', '0b7d9e1a-2c3f-4b5a-9d6e-7f8a9b0c1d2e',
            '0b7d9e1a-2c3f-4b5a-9d6e-7f8a9b0c1d2e', '0b7d9e1a-2c3f-4b5a-9d6e-7f8a9b0c1d2e',
            '1c8e2f3b-4d5a-4c6b-8e7f-9a0b1c2d3e4f', '1c8e2f3b-4d5a-4c6b-8e7f-9a0b1c2d3e4f',
            '1c8e2f3b-4d5a-4c6b-8e7f-9a0b1c2d3e4f', '1c8e2f3b-4d5a-4c6b-8e7f-9a0b1c2d3e4f',
            '1c8e2f3b-4d5a-4c6b-8e7f-9a0b1c2d3e4f', '1c8e2f3b-4d5a-4c6b-8e7f-9a0b1c2d3e4f',
            '1c8e2f3b-4d5a-4c6b-8e7f-9a0b1c2d3e4f', '1c8e2f3b-4d5a-4c6b-8e7f-9a0b1c2d3e4f',
            '2d9f3a4c-5e6b-4d7c-9f8a-0b1c2d3e4f5a', '2d9f3a4c-5e6b-4d7c-9f8a-0b1c2d3e4f5a',
            '2d9f3a4c-5e6b-4d7c-9f8a-0b1c2d3e4f5a', '2d9f3a4c-5e6b-4d7c-9f8a-0b1c2d3e4f5a',
            '2d9f3a4c-5e6b-4d7c-9f8a-0b1c2d3e4f5a', '2d9f3a4c-5e6b-4d7c-9f8a-0b1c2d3e4f5a',
            '2d9f3a4c-5e6b-4d7c-9f8a-0b1c2d3e4f5a', '2d9f3a4c-5e6b-4d7c-9f8a-0b1c2d3e4f5a'
        ]::uuid[] AS cats
) AS t
ON CONFLICT (id) DO UPDATE SET category_id = EXCLUDED.category_id;

COMMIT;
