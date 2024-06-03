-- DROP TABLE public.uber_Analytics_duong;
CREATE TABLE IF NOT EXISTS public.uber_Analytics_duong AS (
SELECT 
	f.vendorid,
	d.tpep_pickup_datetime, 
	d.tpep_dropoff_datetime, 
	ps.passenger_count,
	tr.trip_distance, 
	ra.rate_code_name, 
	up.zone AS pickup_location,
	dr.zone AS droff_location, 
	pa.payment_type_name,
	f.fare_amount, f.extra, f.mta_tax, f.tip_amount, f.tolls_amount,f.total_amount, 
	f.improvement_surcharge
	FROM public.fact_table f
	JOIN public.datetime_dim d ON d.datetime_id = f.datetime_id
	JOIN public.pickup_location_dim up ON up.pickup_location_id = f.pickup_location_id
	JOIN public.dropoff_location_dim dr ON dr.dropoff_location_id = f.dropoff_location_id
	JOIN public.passenger_count_dim ps ON ps.passenger_count_id = f.passenger_count_id
	JOIN public.trip_distance_dim tr ON tr.trip_distance_id = f.trip_distance_id
	JOIN public.rate_code_dim ra ON ra.rate_code_id = f.rate_code_id
	JOIN public.payment_type_dim pa ON pa.payment_type_id = f.payment_type_id)



