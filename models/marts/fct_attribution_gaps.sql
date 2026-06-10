-- Won revenue with no resolvable source lead (null link or dangling key).
select
    o.opportunity_id, o.account_id, o.rep_id,
    o.lead_id,
    o.amount as euro_impact
from {{ ref('stg_opportunities') }} o
left join {{ ref('stg_leads') }} l on o.lead_id = l.lead_id
where o.is_won
  and (o.lead_id is null or l.lead_id is null)
