-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema cap_cadet_tracker_3.0
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema cap_cadet_tracker_3.0
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `cap_cadet_tracker_3.0` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci ;
USE `cap_cadet_tracker_3.0` ;

-- -----------------------------------------------------
-- Table `cap_cadet_tracker_3.0`.`cadet`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cap_cadet_tracker_3.0`.`cadet` (
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
-- Table `cap_cadet_tracker_3.0`.`rank`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cap_cadet_tracker_3.0`.`rank` (
  `rank_id` INT NOT NULL AUTO_INCREMENT,
  `rank_name` VARCHAR(45) NOT NULL,
  `rank_order` INT NOT NULL,
  PRIMARY KEY (`rank_id`),
  UNIQUE INDEX `rank_id_UNIQUE` (`rank_id` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cap_cadet_tracker_3.0`.`pt_score`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cap_cadet_tracker_3.0`.`pt_score` (
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
    REFERENCES `cap_cadet_tracker_3.0`.`cadet` (`cadet_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cap_cadet_tracker_3.0`.`inspection_item`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cap_cadet_tracker_3.0`.`inspection_item` (
  `item_id` INT NOT NULL AUTO_INCREMENT,
  `item_name` VARCHAR(255) NOT NULL,
  `description` TEXT NULL,
  PRIMARY KEY (`item_id`),
  UNIQUE INDEX `item_id_UNIQUE` (`item_id` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cap_cadet_tracker_3.0`.`uniform_inspection`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cap_cadet_tracker_3.0`.`uniform_inspection` (
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
    REFERENCES `cap_cadet_tracker_3.0`.`cadet` (`cadet_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cap_cadet_tracker_3.0`.`uniform_inspection_score`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cap_cadet_tracker_3.0`.`uniform_inspection_score` (
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
    REFERENCES `cap_cadet_tracker_3.0`.`inspection_item` (`item_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_uniform_inspection_score_uniform_inspection1`
    FOREIGN KEY (`uniform_inspection_inspection_id`)
    REFERENCES `cap_cadet_tracker_3.0`.`uniform_inspection` (`inspection_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cap_cadet_tracker_3.0`.`report`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cap_cadet_tracker_3.0`.`report` (
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
    REFERENCES `cap_cadet_tracker_3.0`.`cadet` (`cadet_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cap_cadet_tracker_3.0`.`event`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cap_cadet_tracker_3.0`.`event` (
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
-- Table `cap_cadet_tracker_3.0`.`event_attendance`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cap_cadet_tracker_3.0`.`event_attendance` (
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
    REFERENCES `cap_cadet_tracker_3.0`.`cadet` (`cadet_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_event_attendance_event1`
    FOREIGN KEY (`event_event_id`)
    REFERENCES `cap_cadet_tracker_3.0`.`event` (`event_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cap_cadet_tracker_3.0`.`position`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cap_cadet_tracker_3.0`.`position` (
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
-- Table `cap_cadet_tracker_3.0`.`rank_has_cadet`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cap_cadet_tracker_3.0`.`rank_has_cadet` (
  `rank_rank_id` INT NOT NULL,
  `cadet_cadet_id` INT NOT NULL,
  `date_received` TIMESTAMP NOT NULL,
  PRIMARY KEY (`rank_rank_id`, `cadet_cadet_id`),
  INDEX `fk_rank_has_cadet_cadet1_idx` (`cadet_cadet_id` ASC) VISIBLE,
  INDEX `fk_rank_has_cadet_rank_idx` (`rank_rank_id` ASC) VISIBLE,
  CONSTRAINT `fk_rank_has_cadet_rank`
    FOREIGN KEY (`rank_rank_id`)
    REFERENCES `cap_cadet_tracker_3.0`.`rank` (`rank_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_rank_has_cadet_cadet1`
    FOREIGN KEY (`cadet_cadet_id`)
    REFERENCES `cap_cadet_tracker_3.0`.`cadet` (`cadet_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cap_cadet_tracker_3.0`.`position_has_cadet`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cap_cadet_tracker_3.0`.`position_has_cadet` (
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
    REFERENCES `cap_cadet_tracker_3.0`.`position` (`position_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_position_has_cadet_cadet1`
    FOREIGN KEY (`cadet_cadet_id`)
    REFERENCES `cap_cadet_tracker_3.0`.`cadet` (`cadet_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cap_cadet_tracker_3.0`.`requirement`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cap_cadet_tracker_3.0`.`requirement` (
  `requirement_id` INT NOT NULL AUTO_INCREMENT,
  `requirement_name` VARCHAR(100) NOT NULL,
  `description` TEXT NULL,
  PRIMARY KEY (`requirement_id`),
  UNIQUE INDEX `rank_reqwierment_id_UNIQUE` (`requirement_id` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cap_cadet_tracker_3.0`.`rank_has_requirement`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cap_cadet_tracker_3.0`.`rank_has_requirement` (
  `rank_rank_id` INT NOT NULL,
  `rank_requirement_requirement_id` INT NOT NULL,
  PRIMARY KEY (`rank_rank_id`, `rank_requirement_requirement_id`),
  INDEX `fk_rank_has_rank_requirement_rank_requirement1_idx` (`rank_requirement_requirement_id` ASC) VISIBLE,
  INDEX `fk_rank_has_rank_requirement_rank1_idx` (`rank_rank_id` ASC) VISIBLE,
  CONSTRAINT `fk_rank_has_rank_requirement_rank1`
    FOREIGN KEY (`rank_rank_id`)
    REFERENCES `cap_cadet_tracker_3.0`.`rank` (`rank_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_rank_has_rank_requirement_rank_requirement1`
    FOREIGN KEY (`rank_requirement_requirement_id`)
    REFERENCES `cap_cadet_tracker_3.0`.`requirement` (`requirement_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `cap_cadet_tracker_3.0`.`cadet_has_rank_requirement`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `cap_cadet_tracker_3.0`.`cadet_has_rank_requirement` (
  `cadet_cadet_id` INT NOT NULL,
  `requirement_requirement_id` INT NOT NULL,
  `date_completed` DATE NULL,
  PRIMARY KEY (`cadet_cadet_id`, `requirement_requirement_id`),
  INDEX `fk_cadet_has_rank_requirement_rank_requirement1_idx` (`requirement_requirement_id` ASC) VISIBLE,
  INDEX `fk_cadet_has_rank_requirement_cadet1_idx` (`cadet_cadet_id` ASC) VISIBLE,
  CONSTRAINT `fk_cadet_has_rank_requirement_cadet1`
    FOREIGN KEY (`cadet_cadet_id`)
    REFERENCES `cap_cadet_tracker_3.0`.`cadet` (`cadet_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_cadet_has_rank_requirement_rank_requirement1`
    FOREIGN KEY (`requirement_requirement_id`)
    REFERENCES `cap_cadet_tracker_3.0`.`requirement` (`requirement_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;


