-- Won revenue with no resolvable source lead. Two distinct failure modes get
-- two distinct reason codes: the link was never set, or it points at a lead
-- that no longer exists.
select
    o.opportunity_id, o.account_id, o.rep_id,
    o.lead_id,
    o.amount as euro_impact,
    case when o.lead_id is null then 'closed_won_missing_lead_source'
         else 'closed_won_dangling_lead_reference' end as reason_code
from {{ ref('stg_opportunities') }} o
left join {{ ref('stg_leads') }} l on o.lead_id = l.lead_id
where o.is_won
  and (o.lead_id is null or l.lead_id is null)
