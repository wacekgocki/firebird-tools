-- Info: shows amount of space taken by blobs in tables and columns
-- Credits: StackOverflow question and answers:
-- https://stackoverflow.com/questions/3699921/how-can-i-measure-the-amount-of-space-taken-by-blobs-on-a-firebird-2-1-database

SET TERM #;
EXECUTE BLOCK
RETURNS (BLOB_SIZE BIGINT, TABLENAME CHAR(31), FIELDNAME CHAR(31) )
AS
  DECLARE VARIABLE RN CHAR(31) CHARACTER SET UNICODE_FSS;
  DECLARE VARIABLE FN CHAR(31) CHARACTER SET UNICODE_FSS;
  DECLARE VARIABLE S BIGINT;
BEGIN
  BLOB_SIZE = 0;
  FOR
    SELECT r.rdb$relation_name, r.rdb$field_name 
      FROM rdb$relation_fields r JOIN rdb$fields f 
        ON r.rdb$field_source = f.rdb$field_name
    WHERE f.rdb$field_type = 261
    INTO :RN, :FN
  DO BEGIN
    EXECUTE STATEMENT
      'SELECT SUM(OCTET_LENGTH(' || :FN || ')) AS BLOB_SIZE, ''' || :RN || ''', ''' || :FN || '''
      FROM ' || :RN ||
      ' WHERE NOT ' || :FN || ' IS NULL'
    INTO :BLOB_SIZE, :TABLENAME, :FIELDNAME;
    SUSPEND;
  END
END
#
SET TERM ;#
