INSERT
    OR REPLACE INTO published_prices (
        id,
        building_name,
        year_from,
        month_from,
        year_to,
        month_to,
        price
    )
VALUES
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'Arkadia Green Park'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'Arkadia Green Park',
        2025,
        7,
        2025,
        8,
        2400000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'ASG Tower'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'ASG Tower',
        2025,
        7,
        2025,
        8,
        2800000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'BSD Green Office Park'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'BSD Green Office Park',
        2025,
        7,
        2025,
        8,
        2800000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'Central Park'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'Central Park',
        2025,
        7,
        2025,
        8,
        2800000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'Chubb Square'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'Chubb Square',
        2025,
        7,
        2025,
        8,
        3100000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'Fatmawati'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'Fatmawati',
        2025,
        7,
        2025,
        8,
        2550000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'Kemang X'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'Kemang X',
        2025,
        7,
        2025,
        8,
        2700000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'Lippo Mall Puri'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'Lippo Mall Puri',
        2025,
        7,
        2025,
        8,
        2600000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'Menara Rajawali'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'Menara Rajawali',
        2025,
        7,
        2025,
        8,
        2900000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'Millennium Centennial Center'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'Millennium Centennial Center',
        2025,
        7,
        2025,
        8,
        2900000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'MNC Tower Surabaya'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'MNC Tower Surabaya',
        2025,
        7,
        2025,
        8,
        2250000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'Pacific Place'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'Pacific Place',
        2025,
        7,
        2025,
        8,
        3500000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'Park 23'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'Park 23',
        2025,
        7,
        2025,
        8,
        2900000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'Plaza Indonesia'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'Plaza Indonesia',
        2025,
        7,
        2025,
        8,
        3300000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'Pondok Indah'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'Pondok Indah',
        2025,
        7,
        2025,
        8,
        3000000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'RDTX Square'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'RDTX Square',
        2025,
        7,
        2025,
        8,
        2800000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'Sahid Sudirman'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'Sahid Sudirman',
        2025,
        7,
        2025,
        8,
        2800000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'Sampoerna Strategic Square'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'Sampoerna Strategic Square',
        2025,
        7,
        2025,
        8,
        3000000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'Senayan City'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'Senayan City',
        2025,
        7,
        2025,
        8,
        3400000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'Sinar Mas Land Plaza Medan'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'Sinar Mas Land Plaza Medan',
        2025,
        7,
        2025,
        8,
        2100000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'Sinar Mas Land Plaza Surabaya'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'Sinar Mas Land Plaza Surabaya',
        2025,
        7,
        2025,
        8,
        1800000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'Sopo Del'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'Sopo Del',
        2025,
        7,
        2025,
        8,
        2700000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'Treasury Tower'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'Treasury Tower',
        2025,
        7,
        2025,
        8,
        3500000
    ),
    (
        (
            SELECT
                id
            FROM
                published_prices
            WHERE
                building_name = 'XL Axiata Tower'
                AND year_from = 2025
                AND month_from = 7
                AND year_to = 2025
                AND month_to = 8
        ),
        'XL Axiata Tower',
        2025,
        7,
        2025,
        8,
        2500000
    );