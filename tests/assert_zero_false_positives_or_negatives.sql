-- Calibration test, ID-level. Fails (returns rows) if detection missed any
-- planted leak (false negative) OR flagged anything that was not planted
-- (false positive) - including the planted legitimate exceptions (approved
-- accelerators and credit notes) that a naive check would wrongly accuse.
-- Passing means precision = recall = 100% on the mixed field.
-- For a real client there is no ground-truth seed and this test is dropped.
select *
from {{ ref('fct_audit_calibration') }}
where false_positives > 0 or false_negatives > 0
