CREATE DATABASE portfolio_test;
USE portfolio_test;
GRANT ALL ON portfolio_test TO lyx@'%';


CREATE DATABASE portfolio;
USE portfolio_test;
GRANT ALL ON portfolio_test TO lyx@'%';

ALTER TABLE currency MODIFY updatedAt DATETIME
  DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;