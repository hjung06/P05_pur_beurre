#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymysql.cursors


class MysqlDB:
    """
    Make connection to MySQL server and creates database and tables"""

    def __init__(self, user, password):
        self.user = user
        self.password = password

    def connect(self):

        self.connection = pymysql.connect(host='localhost',
                                          user=self.user,
                                          password=self.password,
                                          charset='utf8mb4',
                                          use_unicode=True,
                                          cursorclass=pymysql.cursors.DictCursor)
    # Check if DB exists

    def check_db(self):

        self.connect()
        try:
            with self.connection.cursor() as cursor:

                sql = 'SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s'
                cursor.execute(sql, ('Openfoodfacts'))

                db = cursor.fetchone()

        finally:
            self.connection.close()

        return db

    # Create databse
    def create_db(self):

        self.connect()

        try:

            # Create database 'openfoodfacts'
            with self.connection.cursor() as cursor:

                sql = ('CREATE DATABASE IF NOT EXISTS Openfoodfacts')
                cursor.execute(sql)
                self.connection.commit()

            # Create talbe 'categories'
            with self.connection.cursor() as cursor:

                sql = ('CREATE TABLE IF NOT EXISTS Openfoodfacts.cat ('
                       'id SMALLINT UNSIGNED AUTO_INCREMENT, '
                       'category VARCHAR(30), '
                       'PRIMARY KEY (id)'
                       ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4')
                cursor.execute(sql)
                self.connection.commit()

            # Create TABLE 'products'
            with self.connection.cursor() as cursor:

                sql = ('CREATE TABLE IF NOT EXISTS Openfoodfacts.Products ('
                       'id SMALLINT UNSIGNED AUTO_INCREMENT, '
                       'code BIGINT UNSIGNED NOT NULL, '
                       'brands VARCHAR(100), '
                       'product_name VARCHAR(200) UNIQUE, '
                       "nutrition_grade_fr ENUM('A','B','C','D','E'), "
                       'stores VARCHAR(100), '
                       'quantity VARCHAR(20), '
                       'ingredients_text TEXT, '
                       'url VARCHAR(300), '
                       'cat_id SMALLINT UNSIGNED, '
                       'PRIMARY KEY (id), '
                       'CONSTRAINT fk_cat_id '
                       'FOREIGN KEY (cat_id) REFERENCES Openfoodfacts.cat(id)'
                       ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4')

                cursor.execute(sql)
                self.connection.commit()

            with self.connection.cursor() as cursor:
                sql = ('CREATE TABLE IF NOT EXISTS Openfoodfacts.My_foods ('
                       'id SMALLINT UNSIGNED AUTO_INCREMENT,'
                       'sub_id SMALLINT UNSIGNED UNIQUE,'
                       'product_id SMALLINT UNSIGNED, '
                       'PRIMARY KEY(id),'
                       'CONSTRAINT fk_sub_id FOREIGN KEY (product_id)'
                       'REFERENCES Openfoodfacts.Products(id),'
                       'CONSTRAINT fk_product_id FOREIGN KEY (product_id)'
                       'REFERENCES Openfoodfacts.Products(id)'
                       ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4')
                cursor.execute(sql)
                self.connection.commit()

        finally:
            self.connection.close()
    # Inert data into cat table

    def insert_categories(self, categories):

        self.categories = categories

        self.connect()

        try:

            with self.connection.cursor() as cursor:

                for category_name in self.categories:

                    sql = ('INSERT INTO Openfoodfacts.Cat (category) VALUES (%s)')

                    cursor.execute(sql, (category_name))
                    self.connection.commit()
        finally:
            self.connection.close()

    # Insert data into product table

    def insert_products(self, data):

        self.data = data

        self.connect()

        try:

            with self.connection.cursor() as cursor:
                cursor.execute('SET NAMES `utf8`')

                for product in self.data:
                    if 'nutrition_grade_fr' in product:
                        grade = product['nutrition_grade_fr']
                        product['nutrition_grade_fr'] = grade.upper()
                    placeholder = ','.join(['%s'] * len(product))
                    columns = ','.join(product.keys())

                    sql = ('INSERT IGNORE INTO Openfoodfacts.Products '
                           '({}) VALUES ({})'.format(columns, placeholder))

                    cursor.execute(sql, (list(product.values())))

                    self.connection.commit()
        finally:
            self.connection.close()
    # Fetch all categories from cat table

    def fetch_categoies(self):

        self.connect()

        try:
            with self.connection.cursor() as cursor:
                sql = 'select * from openfoodfacts.cat'
                cursor.execute(sql)
                return cursor.fetchall()

        finally:
            self.connection.close()
    # Fetch all products selected from category

    def fetch_products(self, cat_id):
        self.cat_id = cat_id
        self.connect()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute('SET @cnt=0')
                sql = ("SELECT (@cnt := @cnt + 1) AS num,"
                       "brands,product_name,id FROM openfoodfacts.products "
                       "WHERE `cat_id`=%s ORDER BY `brands`,`product_name`")
                cursor.execute(sql, (self.cat_id))
                return cursor.fetchall()

        finally:
            self.connection.close()
    # Fetch data of a product

    def fetch_product_info(self, product_id):
        self.product_id = product_id
        self.connect()

        try:
            with self.connection.cursor() as cursor:

                sql = 'SELECT * FROM openfoodfacts.products WHERE `id`=%s'
                cursor.execute(sql, (self.product_id))
                return cursor.fetchall()

        finally:
            self.connection.close()
    # Find highest nutrition score from a category

    def fetch_susbstituts(self, product_id, cat_id):
        self.product_id = product_id
        self.cat_id = cat_id
        self.connect()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute('SET @cnt=0')
                sql = ("SELECT (@cnt := @cnt + 1) AS `num`,"
                       "`brands`, `product_name`, `id`, `cat_id`, `nutrition_grade_fr` "
                       "FROM openfoodfacts.products WHERE id!=%s AND cat_id=%s "
                       "AND nutrition_grade_fr=(SELECT MIN(nutrition_grade_fr) "
                       "FROM Openfoodfacts.products WHERE cat_id=%s) "
                       "ORDER BY `brands`,`product_name` ")
                cursor.execute(sql, (self.product_id, self.cat_id, self.cat_id))
                return cursor.fetchall()
        finally:
            self.connection.close()
    # Insert product selected into my_foods table

    def save_product(self, sub_id, product_id):
        self.sub_id = sub_id
        self.product_id = product_id
        self.connect()

        try:

            with self.connection.cursor() as cursor:
                sql = 'SELECT EXISTS(SELECT 1 FROM Openfoodfacts.my_foods WHERE sub_id=%s) AS check_id'
                cursor.execute(sql, (self.sub_id))
                data_check = cursor.fetchall()
                if data_check[0]['check_id'] == 1:
                    return 'Ce produit déjà existe dans la base de donées'
                else:
                    with self.connection.cursor() as cursor:
                        sql = 'INSERT INTO Openfoodfacts.my_foods (sub_id, product_id) VALUES (%s,%s)'
                        cursor.execute(sql, (self.sub_id, self.product_id))
                        self.connection.commit()
                        message = 'Produit enregistré.'
                        return message

        finally:
            self.connection.close()
    # INNER JOIN my_foods and products table

    def fetch_saved_foods(self):

        self.connect()

        try:
            with self.connection.cursor() as cursor:

                sql = ('SELECT m.id, m.product_id, m.sub_id, p.brands, p.product_name, '
                       'p.cat_id  FROM Openfoodfacts.my_foods AS m '
                       'INNER JOIN Openfoodfacts.Products AS p '
                       'ON m.sub_id=p.id ORDER BY m.id')
                cursor.execute(sql)
                result = cursor.fetchall()
                return result
        finally:
            self.connection.close()
