import environ
import requests
import psycopg2
from datetime import datetime, date, timezone
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
_env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')


def add_movie(movie_id):
    env = _env

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {env('API_TOKEN')}"
    }

    #  Película 
    r = requests.get(
        f'https://api.themoviedb.org/3/movie/{movie_id}?language=en-US',
        headers=headers
    )
    m = r.json()
    print(m)

    #  Imágenes 
    r = requests.get(
        f'https://api.themoviedb.org/3/movie/{movie_id}/images',
        headers=headers
    )
    images = r.json()
    backdrop = images['backdrops'][0]['file_path'] if images.get('backdrops') else None

    #  Conexión DB 
    db_user = env.str('DB_USER', default='').strip() or 'ubuntu'
    conn = psycopg2.connect(
        dbname=env.str('DB_NAME', default='django'),
        user=db_user,
        password=env.str('DB_PASSWORD', default=''),
        host=env.str('DB_HOST', default='/tmp'),
        port=env.str('DB_PORT', default='5432'),
    )
    cur = conn.cursor()

    #  Verificar si la película ya existe 
    cur.execute('SELECT * FROM movies_movie WHERE title = %s', (m['title'],))
    movie_exists = cur.fetchall()
    print(movie_exists)

    #  Créditos 
    r = requests.get(
        f'https://api.themoviedb.org/3/movie/{movie_id}/credits?language=en-US',
        headers=headers
    )
    credits = r.json()

    actors = [
        (actor['id'], actor['name'], actor['known_for_department'], actor.get('profile_path'))
        for actor in credits['cast'][:10]
    ]

    crew = [
        (member['id'], member['name'], member['job'], member.get('profile_path'))
        for member in credits['crew']
        if member['job'] in ['Director', 'Writer', 'Screenplay']
    ]

    credits_list = actors + crew

    #  Datos de cada persona
    persons_data = {}
    for person_id, name, department, profile_path in credits_list:
        r = requests.get(
            f'https://api.themoviedb.org/3/person/{person_id}?language=en-US',
            headers=headers
        )
        data = r.json()
        persons_data[name] = {
            'name': name,
            'profile_path': profile_path,
            'department': department,
            'biography': data.get('biography'),
            'place_of_birth': data.get('place_of_birth'),
            'birthday': data.get('birthday'),
            'gender': data.get('gender')  # 0=No especificado, 1=Femenino, 2=Masculino
        }

    #  Jobs 
    jobs = {job for _, _, job, _ in credits_list}
    print(jobs)

    cur.execute('SELECT * FROM movies_job WHERE name IN %s', (tuple(jobs),))
    jobs_in_db = cur.fetchall()
    existing_job_names = {name for _, name in jobs_in_db}

    jobs_to_create = [(name,) for name in jobs if name not in existing_job_names]
    cur.executemany('INSERT INTO movies_job (name) VALUES (%s)', jobs_to_create)

    #  Personas    
    persons_names = [data['name'] for data in persons_data.values()]

    cur.execute('SELECT name FROM movies_person WHERE name IN %s', (tuple(persons_names),))
    existing_persons = {row[0] for row in cur.fetchall()}

    persons_to_create = [
        (
            data['name'],
            data['profile_path'],
            data['department'],
            data['biography'],
            data['place_of_birth'],
            data['birthday'],
            data['gender']
        )
        for data in persons_data.values()
        if data['name'] not in existing_persons
    ]

    sql_insert_person = '''
        INSERT INTO movies_person
            (name, profile_path, known_for_department, biography, place_of_birth, birthday, gender)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    '''
    cur.executemany(sql_insert_person, persons_to_create)

    #  Géneros 
    genres = [d['name'] for d in m['genres']]
    print(genres)

    cur.execute('SELECT * FROM movies_genre WHERE name IN %s', (tuple(genres),))
    genres_in_db = cur.fetchall()
    existing_genre_names = {name for _, name in genres_in_db}

    genres_to_create = [(name,) for name in genres if name not in existing_genre_names]
    cur.executemany('INSERT INTO movies_genre (name) VALUES (%s)', genres_to_create)

    #  Insertar película 
    date_obj = date.fromisoformat(m['release_date'])
    date_time = datetime.combine(date_obj, datetime.min.time())

    sql_insert_movie = '''
        INSERT INTO movies_movie
            (title, overview, release_date, running_time, budget,
             tmdb_id, revenue, poster_path, backdrops)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''
    movie_tuple = (
        m['title'],
        m['overview'],
        date_time.astimezone(timezone.utc),
        m['runtime'],
        m['budget'],
        movie_id,
        m['revenue'],
        m['poster_path'],
        backdrop
    )
    print(movie_tuple)
    cur.execute(sql_insert_movie, movie_tuple)

    #  Géneros de la película     
    sql_movie_genres = '''
        INSERT INTO movies_movie_genres (movie_id, genre_id)
        SELECT (SELECT id FROM movies_movie WHERE title = %s) AS movie_id,
               id AS genre_id
        FROM movies_genre
        WHERE name IN %s
    '''
    cur.execute(sql_movie_genres, (m['title'], tuple(genres)))

    #  Estudios de producción 
    for company in m.get('production_companies', []):
        cur.execute(
            'SELECT id FROM movies_productioncompany WHERE name = %s',
            (company['name'],)
        )
        existing_company = cur.fetchone()

        if not existing_company:
            cur.execute(
                'INSERT INTO movies_productioncompany (name) VALUES (%s) RETURNING id',
                (company['name'],)
            )
            company_id = cur.fetchone()[0]
        else:
            company_id = existing_company[0]

        cur.execute(
            '''INSERT INTO movies_movie_production_companies (movie_id, productioncompany_id)
               SELECT id, %s FROM movies_movie WHERE title = %s
               ON CONFLICT DO NOTHING''',
            (company_id, m['title'])
    )
    #  Créditos de la película
    print(credits_list)
    sql_credit = '''
        INSERT INTO movies_moviecredit (movie_id, person_id, job_id)
        SELECT id,
               (SELECT id FROM movies_person WHERE name = %s),
               (SELECT id FROM movies_job WHERE name = %s)
        FROM movies_movie
        WHERE title = %s
    '''
    for _, name, job, _ in credits_list:
        cur.execute(sql_credit, (name, job, m['title']))

    conn.commit()
    print("✅ Película agregada correctamente.")


if __name__ == "__main__":
     add_movie(int(sys.argv[1]))
