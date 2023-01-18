\* Source Pyomo model name=Model *\

min 
objective:
+35 flow(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in_0)
+35 flow(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in_1)
+35 flow(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in_2)

s.t.

c_e_Bus_balance(house_1_d_electricity_input_0)_:
+1 flow(house_1_ec_electricity_dist_house_1_d_electricity_input_0)
= 0

c_e_Bus_balance(house_1_d_electricity_input_1)_:
+1 flow(house_1_ec_electricity_dist_house_1_d_electricity_input_1)
= 0.5

c_e_Bus_balance(house_1_d_electricity_input_2)_:
+1 flow(house_1_ec_electricity_dist_house_1_d_electricity_input_2)
= 9

c_e_Bus_balance(house_1_ec_electricity_b_export_0)_:
+1 flow(house_1_ec_electricity_b_export_house_1_ec_electricity_grid_out_0)
= 0

c_e_Bus_balance(house_1_ec_electricity_b_export_1)_:
+1 flow(house_1_ec_electricity_b_export_house_1_ec_electricity_grid_out_1)
= 0

c_e_Bus_balance(house_1_ec_electricity_b_export_2)_:
+1 flow(house_1_ec_electricity_b_export_house_1_ec_electricity_grid_out_2)
= 0

c_e_Bus_balance(house_1_ec_electricity_b_grid_0)_:
-1 flow(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in_0)
+1 flow(house_1_ec_electricity_s_import_house_1_ec_electricity_b_grid_0)
= 0

c_e_Bus_balance(house_1_ec_electricity_b_grid_1)_:
-1 flow(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in_1)
+1 flow(house_1_ec_electricity_s_import_house_1_ec_electricity_b_grid_1)
= 0

c_e_Bus_balance(house_1_ec_electricity_b_grid_2)_:
-1 flow(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in_2)
+1 flow(house_1_ec_electricity_s_import_house_1_ec_electricity_b_grid_2)
= 0

c_e_Bus_balance(house_1_ec_electricity_dist_0)_:
-1 flow(house_1_ec_electricity_dist_house_1_d_electricity_input_0)
+1 flow(house_1_ec_electricity_grid_in_house_1_ec_electricity_dist_0)
+1 flow(house_1_ec_electricity_prod_house_1_ec_electricity_dist_0)
= 0

c_e_Bus_balance(house_1_ec_electricity_dist_1)_:
-1 flow(house_1_ec_electricity_dist_house_1_d_electricity_input_1)
+1 flow(house_1_ec_electricity_grid_in_house_1_ec_electricity_dist_1)
+1 flow(house_1_ec_electricity_prod_house_1_ec_electricity_dist_1)
= 0

c_e_Bus_balance(house_1_ec_electricity_dist_2)_:
-1 flow(house_1_ec_electricity_dist_house_1_d_electricity_input_2)
+1 flow(house_1_ec_electricity_grid_in_house_1_ec_electricity_dist_2)
+1 flow(house_1_ec_electricity_prod_house_1_ec_electricity_dist_2)
= 0

c_e_Bus_balance(house_1_ec_electricity_grid_in_0)_:
+1 flow(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in_0)
-1 flow(house_1_ec_electricity_grid_in_house_1_ec_electricity_dist_0)
= 0

c_e_Bus_balance(house_1_ec_electricity_grid_in_1)_:
+1 flow(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in_1)
-1 flow(house_1_ec_electricity_grid_in_house_1_ec_electricity_dist_1)
= 0

c_e_Bus_balance(house_1_ec_electricity_grid_in_2)_:
+1 flow(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in_2)
-1 flow(house_1_ec_electricity_grid_in_house_1_ec_electricity_dist_2)
= 0

c_e_Bus_balance(house_1_ec_electricity_grid_out_0)_:
+1 flow(house_1_ec_electricity_b_export_house_1_ec_electricity_grid_out_0)
-1 flow(house_1_ec_electricity_grid_out_house_1_ec_electricity_export_0)
= 0

c_e_Bus_balance(house_1_ec_electricity_grid_out_1)_:
+1 flow(house_1_ec_electricity_b_export_house_1_ec_electricity_grid_out_1)
-1 flow(house_1_ec_electricity_grid_out_house_1_ec_electricity_export_1)
= 0

c_e_Bus_balance(house_1_ec_electricity_grid_out_2)_:
+1 flow(house_1_ec_electricity_b_export_house_1_ec_electricity_grid_out_2)
-1 flow(house_1_ec_electricity_grid_out_house_1_ec_electricity_export_2)
= 0

c_e_Bus_balance(house_1_ec_electricity_prod_0)_:
+1 flow(house_1_ec_electricity_prod_house_1_ec_electricity_dist_0)
= 0

c_e_Bus_balance(house_1_ec_electricity_prod_1)_:
+1 flow(house_1_ec_electricity_prod_house_1_ec_electricity_dist_1)
= 0

c_e_Bus_balance(house_1_ec_electricity_prod_2)_:
+1 flow(house_1_ec_electricity_prod_house_1_ec_electricity_dist_2)
= 0

c_u_InvestmentFlow_max(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in_0)_:
-1 InvestmentFlow_invest(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in)
+1 flow(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in_0)
<= 0

c_u_InvestmentFlow_max(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in_1)_:
-1 InvestmentFlow_invest(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in)
+1 flow(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in_1)
<= 0

c_u_InvestmentFlow_max(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in_2)_:
-1 InvestmentFlow_invest(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in)
+1 flow(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in_2)
<= 0

c_e_ONE_VAR_CONSTANT: 
ONE_VAR_CONSTANT = 1.0

bounds
   0 <= flow(house_1_ec_electricity_b_export_house_1_ec_electricity_grid_out_0) <= +inf
   0 <= flow(house_1_ec_electricity_b_export_house_1_ec_electricity_grid_out_1) <= +inf
   0 <= flow(house_1_ec_electricity_b_export_house_1_ec_electricity_grid_out_2) <= +inf
   0 <= flow(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in_0) <= +inf
   0 <= flow(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in_1) <= +inf
   0 <= flow(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in_2) <= +inf
   0 <= flow(house_1_ec_electricity_dist_house_1_d_electricity_input_0) <= +inf
   0 <= flow(house_1_ec_electricity_dist_house_1_d_electricity_input_1) <= +inf
   0 <= flow(house_1_ec_electricity_dist_house_1_d_electricity_input_2) <= +inf
   0 <= flow(house_1_ec_electricity_grid_in_house_1_ec_electricity_dist_0) <= +inf
   0 <= flow(house_1_ec_electricity_grid_in_house_1_ec_electricity_dist_1) <= +inf
   0 <= flow(house_1_ec_electricity_grid_in_house_1_ec_electricity_dist_2) <= +inf
   0 <= flow(house_1_ec_electricity_grid_out_house_1_ec_electricity_export_0) <= +inf
   0 <= flow(house_1_ec_electricity_grid_out_house_1_ec_electricity_export_1) <= +inf
   0 <= flow(house_1_ec_electricity_grid_out_house_1_ec_electricity_export_2) <= +inf
   0 <= flow(house_1_ec_electricity_prod_house_1_ec_electricity_dist_0) <= +inf
   0 <= flow(house_1_ec_electricity_prod_house_1_ec_electricity_dist_1) <= +inf
   0 <= flow(house_1_ec_electricity_prod_house_1_ec_electricity_dist_2) <= +inf
   0 <= flow(house_1_ec_electricity_s_import_house_1_ec_electricity_b_grid_0) <= +inf
   0 <= flow(house_1_ec_electricity_s_import_house_1_ec_electricity_b_grid_1) <= +inf
   0 <= flow(house_1_ec_electricity_s_import_house_1_ec_electricity_b_grid_2) <= +inf
   0 <= InvestmentFlow_invest(house_1_ec_electricity_b_grid_house_1_ec_electricity_grid_in) <= +inf
end
