using System;

// DTOs used by the minimal API
public record CadetCreate(string cap_id, string first_name, string last_name, DateTime? date_of_birth);
public record CadetUpdate(string? cap_id, string? first_name, string? last_name, DateTime? date_of_birth);
public record ReportCreate(int cadet_cadet_id, string report_type, string? description, DateTime? Incident_date, int resolved, string? resolved_by);
public record PositionDto(string position_name, int line, string? level);
public record RequirementCreate(string requirement_name, string? description, int? rank_id);
