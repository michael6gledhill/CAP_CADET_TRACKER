-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema cadet_tracker
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema cadet_tracker
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `cadet_tracker` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci ;
USE `cadet_tracker` ;

-- -----------------------------------------------------
-- Table `cadet_tracker`.`cadet`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cadet_tracker`.`cadet` (
  `cadet_id` INT NOT NULL AUTO_INCREMENT,
  `first_name` VARCHAR(50) NOT NULL,
  `last_name` VARCHAR(50) NOT NULL,
  `date_of_birth` DATE NULL,
  `join_date` DATE NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `cap_id` INT NOT NULL,
  PRIMARY KEY (`cadet_id`),
  UNIQUE INDEX `cadet_id_UNIQUE` (`cadet_id` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cadet_tracker`.`rank`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cadet_tracker`.`rank` (
  `rank_id` INT NOT NULL AUTO_INCREMENT,
  `rank_name` VARCHAR(45) NOT NULL,
  `rank_order` INT NOT NULL,
  PRIMARY KEY (`rank_id`),
  UNIQUE INDEX `rank_id_UNIQUE` (`rank_id` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cadet_tracker`.`pt_score`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cadet_tracker`.`pt_score` (
  `pt_score_id` INT NOT NULL AUTO_INCREMENT,
  `test_date` DATE NOT NULL,
  `pushups` SMALLINT NOT NULL,
  `situps` SMALLINT NOT NULL,
  `mile_run` DECIMAL(4,2) NOT NULL,
  `notes` TEXT NULL,
  `cadet_cadet_id` INT NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`pt_score_id`),
  UNIQUE INDEX `pt_score_id_UNIQUE` (`pt_score_id` ASC) VISIBLE,
  INDEX `fk_pt_score_cadet1_idx` (`cadet_cadet_id` ASC) VISIBLE,
  CONSTRAINT `fk_pt_score_cadet1`
    FOREIGN KEY (`cadet_cadet_id`)
    REFERENCES `cadet_tracker`.`cadet` (`cadet_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cadet_tracker`.`inspection_item`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cadet_tracker`.`inspection_item` (
  `item_id` INT NOT NULL AUTO_INCREMENT,
  `item_name` VARCHAR(255) NOT NULL,
  `description` TEXT NULL,
  PRIMARY KEY (`item_id`),
  UNIQUE INDEX `item_id_UNIQUE` (`item_id` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cadet_tracker`.`uniform_inspection`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cadet_tracker`.`uniform_inspection` (
  `inspection_id` INT NOT NULL AUTO_INCREMENT,
  `inspection_date` DATE NOT NULL,
  `notes` TEXT NULL,
  `cadet_cadet_id` INT NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`inspection_id`),
  UNIQUE INDEX `inspection_id_UNIQUE` (`inspection_id` ASC) VISIBLE,
  INDEX `fk_uniform_inspection_cadet1_idx` (`cadet_cadet_id` ASC) VISIBLE,
  CONSTRAINT `fk_uniform_inspection_cadet1`
    FOREIGN KEY (`cadet_cadet_id`)
    REFERENCES `cadet_tracker`.`cadet` (`cadet_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cadet_tracker`.`uniform_inspection_score`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cadet_tracker`.`uniform_inspection_score` (
  `score_id` INT NOT NULL AUTO_INCREMENT,
  `score` TINYINT NOT NULL,
  `comments` TEXT NULL,
  `inspection_item_item_id` INT NOT NULL,
  `uniform_inspection_inspection_id` INT NOT NULL,
  PRIMARY KEY (`score_id`),
  UNIQUE INDEX `score_id_UNIQUE` (`score_id` ASC) VISIBLE,
  INDEX `fk_uniform_inspection_score_inspection_item1_idx` (`inspection_item_item_id` ASC) VISIBLE,
  INDEX `fk_uniform_inspection_score_uniform_inspection1_idx` (`uniform_inspection_inspection_id` ASC) VISIBLE,
  CONSTRAINT `fk_uniform_inspection_score_inspection_item1`
    FOREIGN KEY (`inspection_item_item_id`)
    REFERENCES `cadet_tracker`.`inspection_item` (`item_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_uniform_inspection_score_uniform_inspection1`
    FOREIGN KEY (`uniform_inspection_inspection_id`)
    REFERENCES `cadet_tracker`.`uniform_inspection` (`inspection_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cadet_tracker`.`report`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cadet_tracker`.`report` (
  `report_id` INT NOT NULL AUTO_INCREMENT,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `report_type` ENUM('Positive', 'Negative') NOT NULL,
  `description` TEXT NOT NULL,
  `created_by` VARCHAR(50) NULL,
  `cadet_cadet_id` INT NOT NULL,
  `Incident_date` DATE NULL,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `resolved` INT NULL,
  `resolved_by` VARCHAR(45) NULL,
  PRIMARY KEY (`report_id`),
  UNIQUE INDEX `report_id_UNIQUE` (`report_id` ASC) VISIBLE,
  INDEX `fk_report_cadet1_idx` (`cadet_cadet_id` ASC) VISIBLE,
  CONSTRAINT `fk_report_cadet1`
    FOREIGN KEY (`cadet_cadet_id`)
    REFERENCES `cadet_tracker`.`cadet` (`cadet_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cadet_tracker`.`event`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cadet_tracker`.`event` (
  `event_id` INT NOT NULL AUTO_INCREMENT,
  `event_name` VARCHAR(100) NOT NULL,
  `event_start_date` DATETIME NOT NULL,
  `event_end_date` DATETIME NOT NULL,
  `location` VARCHAR(100) NOT NULL,
  `notes` TEXT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`event_id`),
  UNIQUE INDEX `event_id_UNIQUE` (`event_id` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cadet_tracker`.`event_attendance`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cadet_tracker`.`event_attendance` (
  `attendance_id` INT NOT NULL AUTO_INCREMENT,
  `attended` TINYINT NOT NULL,
  `notes` TEXT NULL,
  `cadet_cadet_id` INT NOT NULL,
  `event_event_id` INT NOT NULL,
  PRIMARY KEY (`attendance_id`, `cadet_cadet_id`, `event_event_id`),
  UNIQUE INDEX `attendance_id_UNIQUE` (`attendance_id` ASC) VISIBLE,
  INDEX `fk_event_attendance_cadet1_idx` (`cadet_cadet_id` ASC) VISIBLE,
  INDEX `fk_event_attendance_event1_idx` (`event_event_id` ASC) VISIBLE,
  CONSTRAINT `fk_event_attendance_cadet1`
    FOREIGN KEY (`cadet_cadet_id`)
    REFERENCES `cadet_tracker`.`cadet` (`cadet_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_event_attendance_event1`
    FOREIGN KEY (`event_event_id`)
    REFERENCES `cadet_tracker`.`event` (`event_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cadet_tracker`.`position`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cadet_tracker`.`position` (
  `position_id` INT NOT NULL AUTO_INCREMENT,
  `position_name` VARCHAR(100) NOT NULL,
  `description` TEXT NULL,
  `level` INT NOT NULL,
  `reports_to_position_id` INT NULL,
  `line` TINYINT NOT NULL,
  PRIMARY KEY (`position_id`),
  UNIQUE INDEX `position_id_UNIQUE` (`position_id` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cadet_tracker`.`rank_has_cadet`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cadet_tracker`.`rank_has_cadet` (
  `rank_rank_id` INT NOT NULL,
  `cadet_cadet_id` INT NOT NULL,
  `date_received` TIMESTAMP NOT NULL,
  PRIMARY KEY (`rank_rank_id`, `cadet_cadet_id`),
  INDEX `fk_rank_has_cadet_cadet1_idx` (`cadet_cadet_id` ASC) VISIBLE,
  INDEX `fk_rank_has_cadet_rank_idx` (`rank_rank_id` ASC) VISIBLE,
  CONSTRAINT `fk_rank_has_cadet_rank`
    FOREIGN KEY (`rank_rank_id`)
    REFERENCES `cadet_tracker`.`rank` (`rank_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_rank_has_cadet_cadet1`
    FOREIGN KEY (`cadet_cadet_id`)
    REFERENCES `cadet_tracker`.`cadet` (`cadet_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cadet_tracker`.`position_has_cadet`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cadet_tracker`.`position_has_cadet` (
  `position_has_cadet_id` INT NOT NULL AUTO_INCREMENT,
  `position_position_id` INT NOT NULL,
  `cadet_cadet_id` INT NOT NULL,
  `start_date` TIMESTAMP NULL,
  `end_date` DATE NULL,
  `notes` TEXT NULL,
  PRIMARY KEY (`position_has_cadet_id`),
  INDEX `fk_position_has_cadet_cadet1_idx` (`cadet_cadet_id` ASC) VISIBLE,
  INDEX `fk_position_has_cadet_position1_idx` (`position_position_id` ASC) VISIBLE,
  UNIQUE INDEX `position_has_cade_id_UNIQUE` (`position_has_cadet_id` ASC) VISIBLE,
  CONSTRAINT `fk_position_has_cadet_position1`
    FOREIGN KEY (`position_position_id`)
    REFERENCES `cadet_tracker`.`position` (`position_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_position_has_cadet_cadet1`
    FOREIGN KEY (`cadet_cadet_id`)
    REFERENCES `cadet_tracker`.`cadet` (`cadet_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cadet_tracker`.`requirement`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cadet_tracker`.`requirement` (
  `requirement_id` INT NOT NULL AUTO_INCREMENT,
  `requirement_name` VARCHAR(100) NOT NULL,
  `description` TEXT NULL,
  PRIMARY KEY (`requirement_id`),
  UNIQUE INDEX `rank_reqwierment_id_UNIQUE` (`requirement_id` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cadet_tracker`.`rank_has_requirement`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cadet_tracker`.`rank_has_requirement` (
  `rank_rank_id` INT NOT NULL,
  `rank_requirement_requirement_id` INT NOT NULL,
  PRIMARY KEY (`rank_rank_id`, `rank_requirement_requirement_id`),
  INDEX `fk_rank_has_rank_requirement_rank_requirement1_idx` (`rank_requirement_requirement_id` ASC) VISIBLE,
  INDEX `fk_rank_has_rank_requirement_rank1_idx` (`rank_rank_id` ASC) VISIBLE,
  CONSTRAINT `fk_rank_has_rank_requirement_rank1`
    FOREIGN KEY (`rank_rank_id`)
    REFERENCES `cadet_tracker`.`rank` (`rank_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_rank_has_rank_requirement_rank_requirement1`
    FOREIGN KEY (`rank_requirement_requirement_id`)
    REFERENCES `cadet_tracker`.`requirement` (`requirement_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cadet_tracker`.`cadet_has_rank_requirement`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cadet_tracker`.`cadet_has_rank_requirement` (
  `cadet_cadet_id` INT NOT NULL,
  `requirement_requirement_id` INT NOT NULL,
  `date_completed` DATE NULL,
  PRIMARY KEY (`cadet_cadet_id`, `requirement_requirement_id`),
  INDEX `fk_cadet_has_rank_requirement_rank_requirement1_idx` (`requirement_requirement_id` ASC) VISIBLE,
  INDEX `fk_cadet_has_rank_requirement_cadet1_idx` (`cadet_cadet_id` ASC) VISIBLE,
  CONSTRAINT `fk_cadet_has_rank_requirement_cadet1`
    FOREIGN KEY (`cadet_cadet_id`)
    REFERENCES `cadet_tracker`.`cadet` (`cadet_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_cadet_has_rank_requirement_rank_requirement1`
    FOREIGN KEY (`requirement_requirement_id`)
    REFERENCES `cadet_tracker`.`requirement` (`requirement_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;





INSERT INTO `cadet_tracker`.`position` 
(position_name, description, level, reports_to_position_id, line)
VALUES
-- LINE POSITIONS
('Cadet', 'Entry-level cadet position', 1, NULL, 1),
('Element Leader', 'Leads a small group of cadets', 2, 1, 1),
('Flight Sergeant', 'Oversees a flight of cadets', 3, 2, 1),
('First Sergeant', 'Senior NCO supporting flight operations', 4, 3, 1),
('Flight Commander', 'Commands a flight within the squadron', 5, 3, 1),
('Deputy Commander', 'Second-in-command of the squadron', 6, NULL, 1),
('Cadet Commander', 'Leads the entire cadet corps', 7, NULL, 1),

-- SUPPORT STAFF POSITIONS
('Admin Officer', 'Manages records and administration', 3, 6, 0),
('Admin NCO', 'Assists Admin Officer with administrative tasks', 2, 8, 0),

('Aerospace Education Officer', 'Oversees AE program', 3, 6, 0),
('Aerospace Education NCO', 'Assists AE Officer with AE instruction', 2, 10, 0),

('Leadership Officer', 'Coordinates leadership training', 3, 6, 0),
('Leadership NCO', 'Assists Leadership Officer with training sessions', 2, 12, 0),

('Logistics Officer', 'Responsible for supply and equipment', 3, 6, 0),
('Logistics NCO', 'Manages issue and tracking of equipment', 2, 14, 0),

('Safety Officer', 'Ensures safety protocols are followed', 3, 6, 0),

('Public Affairs Officer', 'Handles newsletters, social media, and PR', 3, 6, 0),
('Public Affairs NCO', 'Assists PA Officer with communications', 2, 17, 0),

('Operations Officer', 'Plans and coordinates squadron events', 3, 6, 0),
('Operations NCO', 'Assists Ops Officer with event logistics', 2, 19, 0);


INSERT INTO `cadet_tracker`.`rank` (rank_name, rank_order)
VALUES
-- PHASE I - THE LEARNING PHASE
('C/Amn', 1),
('C/A1C', 2),
('C/SrA', 3),
('C/SSgt', 4),

-- PHASE II - THE LEADERSHIP PHASE
('C/TSgt', 5),
('C/MSgt', 6),
('C/SMSgt', 7),
('C/CMSgt', 8),
('C/CMSgt', 9),
('C/2d Lt', 10),

-- PHASE III - THE COMMAND PHASE
('C/2d Lt', 11),
('C/1st Lt', 12),
('C/1st Lt', 13),
('C/Capt', 14),

-- PHASE IV - THE EXECUTIVE PHASE
('C/Capt', 15),
('C/Capt', 16),
('C/Maj', 17),
('C/Maj', 18),
('C/Maj', 19),
('C/Lt Col', 20),

-- PINNACLE
('C/Col', 21);


INSERT INTO `cadet_tracker`.`cadet` (first_name, last_name, cap_id)
VALUES
('Miley', 'Barbee', 727171),
('Jack', 'Boren', 627637),
('Raylan', 'Burlison', 752562),
('Gavyn', 'Butler', 694823),
('Kale', 'Collard', 744396),
('Hannah', 'Covell', 753301),
('Tarin', 'Crowder', 709079),
('Jonathan', 'Deloach', 754548),
('Evelyn', 'Ferguson', 686181),
('Morgan', 'Fruth', 665553),
('Garrett', 'Fruth', 720852),
('Nicholas', 'Gingerich', 681612),
('Michael', 'Gledhill', 706704),
('Samuel', 'Grinnell', 733183),
('Jonathan', 'Grinnell', 745148),
('Carson', 'Henrion', 717978),
('Ariel', 'Hiser', 709399),
('Caleb', 'Johnson', 748235),
('Dorian', 'Jones', 752545),
('Nathaniel', 'Lewis', 743703),
('Levi', 'McCaslin', 710892),
('Josiah', 'Miller', 743626),
('Justice', 'Morgan', 734307),
('Matthias', 'Morgan', 734306),
('Autumn', 'Morgan', 714744),
('Reid', 'Neal', 754724),
('Jason', 'Nunes Jr', 733232),
('Walter', 'Perez', 750714),
('Nolan', 'Reyes', 726971),
('Isabel', 'Reyes', 747188),
('Carter', 'Sapp', 755130),
('William', 'Schultz', 754184),
('Trenton', 'Moore', 753940),
('Ariella', 'White', 753920),
('Paul', 'Williams', 733062),
('Mia', 'Yates', 695203);

