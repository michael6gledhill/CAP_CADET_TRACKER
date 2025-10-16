using MySqlConnector;
using System.Text.Json;

// DTOs are declared in Dtos.cs to avoid mixing top-level statements and type declarations

public class Program
{
    public static async Task Main(string[] args)
    {
        var builder = WebApplication.CreateBuilder(args);

        builder.Services.AddCors(options =>
        {
            options.AddDefaultPolicy(policy =>
                policy.AllowAnyOrigin().AllowAnyHeader().AllowAnyMethod());
        });

        builder.WebHost.UseUrls("http://localhost:5057");
        var app = builder.Build();
        app.UseCors();
        app.MapGet("/", () => Results.Ok(new { ok = true, service = "CadetTracker API" }));

        // Config
        var cs = new MySqlConnectionStringBuilder
        {
            Server = "127.0.0.1",
            Port = 3306,
            UserID = "Michael",
            Password = "hogbog89",
            Database = "cadet_tracker",
            SslMode = MySqlSslMode.None, // local
            AllowPublicKeyRetrieval = true, // enable RSA key retrieval if required
            ConnectionTimeout = 8,
            DefaultCommandTimeout = 15,
        };

        string Redact(string connStr)
        {
            var b = new MySqlConnectionStringBuilder(connStr) { Password = "****" };
            return b.ConnectionString;
        }

        app.MapGet("/api/test", async () =>
        {
            try
            {
                await using var conn = new MySqlConnection(cs.ConnectionString);
                await conn.OpenAsync();
                await using var cmd = new MySqlCommand("SELECT 1", conn);
                var val = await cmd.ExecuteScalarAsync();
                return Results.Ok(new { ok = val });
            }
            catch (Exception ex)
            {
                return Results.Ok(new { error = ex.Message, stack = ex.StackTrace, conn = Redact(cs.ConnectionString) });
            }
        });

// DTOs are declared in Dtos.cs

// Cadets: list, search, get, create, update, delete
app.MapGet("/api/cadets/search", async (string? q) =>
{
    try
    {
        await using var conn = new MySqlConnection(cs.ConnectionString);
        await conn.OpenAsync();
        string sql;
        if (!string.IsNullOrWhiteSpace(q))
        {
            sql = "SELECT cadet_id, cap_id, first_name, last_name, date_of_birth FROM cadet WHERE CONCAT(first_name, ' ', last_name) LIKE @like OR CAST(cap_id AS CHAR) LIKE @like ORDER BY last_name, first_name LIMIT 200";
            await using var cmd = new MySqlCommand(sql, conn);
            cmd.Parameters.AddWithValue("@like", $"%{q}%");
            await using var reader = await cmd.ExecuteReaderAsync();
            var list = new List<object>();
            while (await reader.ReadAsync())
            {
                list.Add(new { cadet_id = reader["cadet_id"], cap_id = reader["cap_id"], first_name = reader["first_name"], last_name = reader["last_name"], date_of_birth = reader["date_of_birth"] });
            }
            return Results.Ok(list);
        }
        else
        {
            sql = "SELECT cadet_id, cap_id, first_name, last_name, date_of_birth FROM cadet ORDER BY last_name, first_name LIMIT 200";
            await using var cmd = new MySqlCommand(sql, conn);
            await using var reader = await cmd.ExecuteReaderAsync();
            var list = new List<object>();
            while (await reader.ReadAsync())
            {
                list.Add(new { cadet_id = reader["cadet_id"], cap_id = reader["cap_id"], first_name = reader["first_name"], last_name = reader["last_name"], date_of_birth = reader["date_of_birth"] });
            }
            return Results.Ok(list);
        }
    }
    catch (Exception ex)
    {
        return Results.Ok(new { error = ex.Message, stack = ex.StackTrace });
    }
});

app.MapGet("/api/cadets/{id:int}", async (int id) =>
{
    try
    {
        await using var conn = new MySqlConnection(cs.ConnectionString);
        await conn.OpenAsync();
        await using var cmd = new MySqlCommand("SELECT cadet_id, cap_id, first_name, last_name, date_of_birth FROM cadet WHERE cadet_id=@id", conn);
        cmd.Parameters.AddWithValue("@id", id);
        await using var reader = await cmd.ExecuteReaderAsync();
        if (await reader.ReadAsync())
        {
            return Results.Ok(new { cadet_id = reader["cadet_id"], cap_id = reader["cap_id"], first_name = reader["first_name"], last_name = reader["last_name"], date_of_birth = reader["date_of_birth"] });
        }
        return Results.NotFound();
    }
    catch (Exception ex)
    {
        return Results.Ok(new { error = ex.Message, stack = ex.StackTrace });
    }
});

app.MapPost("/api/cadets", async (CadetCreate body) =>
{
    try
    {
        await using var conn = new MySqlConnection(cs.ConnectionString);
        await conn.OpenAsync();
        await using var cmd = new MySqlCommand("INSERT INTO cadet (cap_id, first_name, last_name, date_of_birth) VALUES (@cap,@first,@last,@dob); SELECT LAST_INSERT_ID();", conn);
        cmd.Parameters.AddWithValue("@cap", body.cap_id);
        cmd.Parameters.AddWithValue("@first", body.first_name);
        cmd.Parameters.AddWithValue("@last", body.last_name);
        cmd.Parameters.AddWithValue("@dob", (object?)body.date_of_birth ?? DBNull.Value);
        var id = Convert.ToInt32(await cmd.ExecuteScalarAsync());
        return Results.Ok(new { cadet_id = id });
    }
    catch (Exception ex)
    {
        return Results.Ok(new { error = ex.Message, stack = ex.StackTrace });
    }
});

app.MapPut("/api/cadets/{id:int}", async (int id, CadetUpdate body) =>
{
    try
    {
        await using var conn = new MySqlConnection(cs.ConnectionString);
        await conn.OpenAsync();
        var sql = "UPDATE cadet SET cap_id = COALESCE(@cap, cap_id), first_name = COALESCE(@first, first_name), last_name = COALESCE(@last, last_name), date_of_birth = COALESCE(@dob, date_of_birth) WHERE cadet_id=@id";
        await using var cmd = new MySqlCommand(sql, conn);
        cmd.Parameters.AddWithValue("@cap", (object?)body.cap_id ?? DBNull.Value);
        cmd.Parameters.AddWithValue("@first", (object?)body.first_name ?? DBNull.Value);
        cmd.Parameters.AddWithValue("@last", (object?)body.last_name ?? DBNull.Value);
        cmd.Parameters.AddWithValue("@dob", (object?)body.date_of_birth ?? DBNull.Value);
        cmd.Parameters.AddWithValue("@id", id);
        var affected = await cmd.ExecuteNonQueryAsync();
        return Results.Ok(new { affected });
    }
    catch (Exception ex)
    {
        return Results.Ok(new { error = ex.Message, stack = ex.StackTrace });
    }
});

app.MapDelete("/api/cadets/{id:int}", async (int id) =>
{
    try
    {
        await using var conn = new MySqlConnection(cs.ConnectionString);
        await conn.OpenAsync();
        await using var cmd = new MySqlCommand("DELETE FROM cadet WHERE cadet_id=@id", conn);
        cmd.Parameters.AddWithValue("@id", id);
        var affected = await cmd.ExecuteNonQueryAsync();
        return Results.Ok(new { affected });
    }
    catch (Exception ex)
    {
        return Results.Ok(new { error = ex.Message, stack = ex.StackTrace });
    }
});

// Reports: create and delete
app.MapPost("/api/reports", async (ReportCreate body) =>
{
    try
    {
        await using var conn = new MySqlConnection(cs.ConnectionString);
        await conn.OpenAsync();
        await using var cmd = new MySqlCommand("INSERT INTO report (cadet_cadet_id, report_type, description, created_by, Incident_date, resolved, resolved_by) VALUES (@cid,@type,@desc,NULL,@date,@resolved,@resolved_by); SELECT LAST_INSERT_ID();", conn);
        cmd.Parameters.AddWithValue("@cid", body.cadet_cadet_id);
        cmd.Parameters.AddWithValue("@type", body.report_type);
        cmd.Parameters.AddWithValue("@desc", (object?)body.description ?? DBNull.Value);
        cmd.Parameters.AddWithValue("@date", (object?)body.Incident_date ?? DBNull.Value);
        cmd.Parameters.AddWithValue("@resolved", body.resolved);
        cmd.Parameters.AddWithValue("@resolved_by", (object?)body.resolved_by ?? DBNull.Value);
        var id = Convert.ToInt32(await cmd.ExecuteScalarAsync());
        return Results.Ok(new { report_id = id });
    }
    catch (Exception ex)
    {
        return Results.Ok(new { error = ex.Message, stack = ex.StackTrace });
    }
});

app.MapDelete("/api/reports/{id:int}", async (int id) =>
{
    try
    {
        await using var conn = new MySqlConnection(cs.ConnectionString);
        await conn.OpenAsync();
        await using var cmd = new MySqlCommand("DELETE FROM report WHERE report_id=@id", conn);
        cmd.Parameters.AddWithValue("@id", id);
        var affected = await cmd.ExecuteNonQueryAsync();
        return Results.Ok(new { affected });
    }
    catch (Exception ex)
    {
        return Results.Ok(new { error = ex.Message, stack = ex.StackTrace });
    }
});

// Positions: list, create, update, delete (unlink cadets)
app.MapGet("/api/positions", async () =>
{
    try
    {
        await using var conn = new MySqlConnection(cs.ConnectionString);
        await conn.OpenAsync();
        await using var cmd = new MySqlCommand("SELECT position_id, position_name, line, level FROM `position` ORDER BY position_id", conn);
        await using var reader = await cmd.ExecuteReaderAsync();
        var list = new List<object>();
        while (await reader.ReadAsync())
        {
            list.Add(new { position_id = reader["position_id"], position_name = reader["position_name"], line = reader["line"], level = reader["level"] });
        }
        return Results.Ok(list);
    }
    catch (Exception ex)
    {
        return Results.Ok(new { error = ex.Message, stack = ex.StackTrace });
    }
});

app.MapPost("/api/positions", async (PositionDto body) =>
{
    try
    {
        await using var conn = new MySqlConnection(cs.ConnectionString);
        await conn.OpenAsync();
        await using var cmd = new MySqlCommand("INSERT INTO `position` (position_name, line, level) VALUES (@name,@line,@level); SELECT LAST_INSERT_ID();", conn);
        cmd.Parameters.AddWithValue("@name", body.position_name);
        cmd.Parameters.AddWithValue("@line", body.line);
        cmd.Parameters.AddWithValue("@level", (object?)body.level ?? DBNull.Value);
        var id = Convert.ToInt32(await cmd.ExecuteScalarAsync());
        return Results.Ok(new { position_id = id });
    }
    catch (Exception ex)
    {
        return Results.Ok(new { error = ex.Message, stack = ex.StackTrace });
    }
});

app.MapPut("/api/positions/{id:int}", async (int id, PositionDto body) =>
{
    try
    {
        await using var conn = new MySqlConnection(cs.ConnectionString);
        await conn.OpenAsync();
        await using var cmd = new MySqlCommand("UPDATE `position` SET position_name=@name, line=@line, level=@level WHERE position_id=@id", conn);
        cmd.Parameters.AddWithValue("@name", body.position_name);
        cmd.Parameters.AddWithValue("@line", body.line);
        cmd.Parameters.AddWithValue("@level", (object?)body.level ?? DBNull.Value);
        cmd.Parameters.AddWithValue("@id", id);
        var affected = await cmd.ExecuteNonQueryAsync();
        return Results.Ok(new { affected });
    }
    catch (Exception ex)
    {
        return Results.Ok(new { error = ex.Message, stack = ex.StackTrace });
    }
});

app.MapDelete("/api/positions/{id:int}", async (int id) =>
{
    try
    {
        await using var conn = new MySqlConnection(cs.ConnectionString);
        await conn.OpenAsync();
        // unlink cadets then delete
        await using var t = await conn.BeginTransactionAsync();
        await using var cmd1 = new MySqlCommand("DELETE FROM position_has_cadet WHERE position_position_id=@id", conn, t);
        cmd1.Parameters.AddWithValue("@id", id);
        await cmd1.ExecuteNonQueryAsync();
        await using var cmd2 = new MySqlCommand("DELETE FROM `position` WHERE position_id=@id", conn, t);
        cmd2.Parameters.AddWithValue("@id", id);
        var affected = await cmd2.ExecuteNonQueryAsync();
        await t.CommitAsync();
        return Results.Ok(new { affected });
    }
    catch (Exception ex)
    {
        return Results.Ok(new { error = ex.Message, stack = ex.StackTrace });
    }
});

// Requirements: list ranks, list requirements for rank, create & link, unlink
app.MapGet("/api/ranks", async () =>
{
    try
    {
        await using var conn = new MySqlConnection(cs.ConnectionString);
        await conn.OpenAsync();
        await using var cmd = new MySqlCommand("SELECT rank_id, rank_name FROM `rank` ORDER BY rank_order ASC", conn);
        await using var reader = await cmd.ExecuteReaderAsync();
        var list = new List<object>();
        while (await reader.ReadAsync())
        {
            list.Add(new { id = reader["rank_id"], name = reader["rank_name"] });
        }
        return Results.Ok(list);
    }
    catch (Exception ex)
    {
        return Results.Ok(new { error = ex.Message, stack = ex.StackTrace });
    }
});

app.MapGet("/api/requirements", async (int rank_id) =>
{
    try
    {
        await using var conn = new MySqlConnection(cs.ConnectionString);
        await conn.OpenAsync();
        await using var cmd = new MySqlCommand(@"SELECT r.requirement_id, r.requirement_name, r.description
          FROM rank_has_requirement rr
          JOIN requirement r ON rr.rank_requirement_requirement_id = r.requirement_id
          WHERE rr.rank_rank_id = @rank
          ORDER BY r.requirement_id", conn);
        cmd.Parameters.AddWithValue("@rank", rank_id);
        await using var reader = await cmd.ExecuteReaderAsync();
        var list = new List<object>();
        while (await reader.ReadAsync())
        {
            list.Add(new { id = reader["requirement_id"], name = reader["requirement_name"], desc = reader["description"] });
        }
        return Results.Ok(list);
    }
    catch (Exception ex)
    {
        return Results.Ok(new { error = ex.Message, stack = ex.StackTrace });
    }
});

app.MapPost("/api/requirements", async (RequirementCreate body) =>
{
    try
    {
        await using var conn = new MySqlConnection(cs.ConnectionString);
        await conn.OpenAsync();
        await using var t = await conn.BeginTransactionAsync();
        await using var cmd = new MySqlCommand("INSERT INTO requirement (requirement_name, description) VALUES (@name,@desc); SELECT LAST_INSERT_ID();", conn, t);
        cmd.Parameters.AddWithValue("@name", body.requirement_name);
        cmd.Parameters.AddWithValue("@desc", (object?)body.description ?? DBNull.Value);
        var reqId = Convert.ToInt32(await cmd.ExecuteScalarAsync());
        if (body.rank_id.HasValue)
        {
            await using var link = new MySqlCommand("INSERT INTO rank_has_requirement (rank_rank_id, rank_requirement_requirement_id) VALUES (@rank,@req)", conn, t);
            link.Parameters.AddWithValue("@rank", body.rank_id.Value);
            link.Parameters.AddWithValue("@req", reqId);
            await link.ExecuteNonQueryAsync();
        }
        await t.CommitAsync();
        return Results.Ok(new { requirement_id = reqId });
    }
    catch (Exception ex)
    {
        return Results.Ok(new { error = ex.Message, stack = ex.StackTrace });
    }
});

app.MapDelete("/api/requirements/unlink", async (int rank_id, int req_id) =>
{
    try
    {
        await using var conn = new MySqlConnection(cs.ConnectionString);
        await conn.OpenAsync();
        await using var cmd = new MySqlCommand("DELETE FROM rank_has_requirement WHERE rank_rank_id=@rank AND rank_requirement_requirement_id=@req", conn);
        cmd.Parameters.AddWithValue("@rank", rank_id);
        cmd.Parameters.AddWithValue("@req", req_id);
        var affected = await cmd.ExecuteNonQueryAsync();
        return Results.Ok(new { affected });
    }
    catch (Exception ex)
    {
        return Results.Ok(new { error = ex.Message, stack = ex.StackTrace });
    }
});

app.MapGet("/api/cadets", async () =>
{
    try
    {
        await using var conn = new MySqlConnection(cs.ConnectionString);
        await conn.OpenAsync();
        await using var cmd = new MySqlCommand("SELECT cadet_id, cap_id, first_name, last_name, date_of_birth FROM cadet ORDER BY last_name, first_name LIMIT 200", conn);
        await using var reader = await cmd.ExecuteReaderAsync();
        var list = new List<object>();
        while (await reader.ReadAsync())
        {
            list.Add(new
            {
                cadet_id = reader["cadet_id"],
                cap_id = reader["cap_id"],
                first_name = reader["first_name"],
                last_name = reader["last_name"],
                date_of_birth = reader["date_of_birth"]
            });
        }
        return Results.Ok(list);
    }
    catch (Exception ex)
    {
        return Results.Ok(new { error = ex.Message, stack = ex.StackTrace, conn = Redact(cs.ConnectionString) });
    }
});

app.MapGet("/api/reports", async () =>
{
    try
    {
        await using var conn = new MySqlConnection(cs.ConnectionString);
        await conn.OpenAsync();
        await using var cmd = new MySqlCommand("SELECT report_id, cadet_cadet_id, report_type, Incident_date, resolved FROM report ORDER BY Incident_date DESC LIMIT 500", conn);
        await using var reader = await cmd.ExecuteReaderAsync();
        var list = new List<object>();
        while (await reader.ReadAsync())
        {
            list.Add(new
            {
                report_id = reader["report_id"],
                cadet_cadet_id = reader["cadet_cadet_id"],
                report_type = reader["report_type"],
                Incident_date = reader["Incident_date"],
                resolved = reader["resolved"]
            });
        }
        return Results.Ok(list);
    }
    catch (Exception ex)
    {
        return Results.Ok(new { error = ex.Message, stack = ex.StackTrace, conn = Redact(cs.ConnectionString) });
    }
});

app.MapGet("/api/diag", async () =>
{
    try
    {
        await using var conn = new MySqlConnection(cs.ConnectionString);
        await conn.OpenAsync();
        var serverVersion = conn.ServerVersion;
    var database = (string?)await new MySqlCommand("SELECT DATABASE()", conn).ExecuteScalarAsync();
        return Results.Ok(new
        {
            ok = true,
            serverVersion,
            database,
            connection = Redact(cs.ConnectionString)
        });
    }
    catch (Exception ex)
    {
        return Results.Ok(new { error = ex.Message, stack = ex.StackTrace, conn = Redact(cs.ConnectionString) });
    }
});

        await app.RunAsync();
    }
}
