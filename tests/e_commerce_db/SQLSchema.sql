
-- run following commands in mysql shell to create a local db

CREATE DATABASE e_commerce_db;

USE e_commerce_db

CREATE TABLE Customers (
  id INT PRIMARY KEY,
  first_name VARCHAR(50) NOT NULL,
  last_name VARCHAR(50) NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  password VARCHAR(100) NOT NULL
);

CREATE TABLE Products (
  id INT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description TEXT NOT NULL,
  price DECIMAL(10, 2) NOT NULL,
  image_url VARCHAR(500) NOT NULL
);

CREATE TABLE Orders (
  id INT PRIMARY KEY,
  customer_id INT NOT NULL,
  order_date DATETIME NOT NULL,
  total DECIMAL(10, 2) NOT NULL,
  FOREIGN KEY (customer_id) REFERENCES Customers(id)
);

CREATE TABLE Order_Items (
  id INT PRIMARY KEY,
  order_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT NOT NULL,
  price DECIMAL(10, 2) NOT NULL,
  FOREIGN KEY (order_id) REFERENCES Orders(id),
  FOREIGN KEY (product_id) REFERENCES Products(id)
);

CREATE TABLE Reviews (
  id INT PRIMARY KEY,
  customer_id INT NOT NULL,
  product_id INT NOT NULL,
  rating INT NOT NULL,
  comment TEXT,
  FOREIGN KEY (customer_id) REFERENCES Customers(id),
  FOREIGN KEY (product_id) REFERENCES Products(id)
);


INSERT INTO Customers (id, first_name, last_name, email, password)
VALUES (1, 'John', 'Doe', 'johndoe@gmail.com', 'password123'),
(2, 'Jane', 'Doe', 'janedoe@yahoo.com', 'password456'),
(3, 'Bob', 'Smith', 'bobsmith@hotmail.com', 'password789');

INSERT INTO Products (id, name, description, price, image_url)
VALUES (1, 'Product A', 'Description of Product A', 10.99, 'http://example.com/product-a.jpg'),
(2, 'Product B', 'Description of Product B', 24.99, 'http://example.com/product-b.jpg'),
(3, 'Product C', 'Description of Product C', 5.99, 'http://example.com/product-c.jpg');

INSERT INTO Orders (id, customer_id, order_date, total)
VALUES (1, 1, '2023-04-01 14:30:00', 35.97),
(2, 2, '2023-04-02 10:15:00', 24.99),
(3, 3, '2023-04-03 16:45:00', 10.99);

INSERT INTO Order_Items (id, order_id, product_id, quantity, price)
VALUES (1, 1, 1, 2, 10.99),
(2, 1, 3, 1, 5.99),
(3, 2, 2, 1, 24.99),
(4, 3, 1, 1, 10.99),
(5, 3, 3, 1, 5.99);

INSERT INTO Reviews (id, customer_id, product_id, rating, comment)
VALUES (1, 1, 2, 4, 'Great product!'),
(2, 2, 1, 3, 'Average product.'),
(3, 3, 3, 5, 'Excellent product! Highly recommended!');