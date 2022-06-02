#!/usr/intel/pkgs/perl/5.8.7/bin/perl 
BEGIN {push @INC, $ENV{HTD_ROOT}.'/htd_info/'};
use info_service_client;

#print "RESP:".&info_service_client::get_cr_address_by_name(ui=>"cr_info",name=>"MCHBAR_0_0_0_PCI",regfile_filter_str=>"iop_registers_bank");
#print "RESP:".&info_service_client::get_cr_property_by_name(ui=>"cr_info",name=>"MCHBAR_0_0_0_PCI",property_str=>"portid",regfile_filter_str=>"iop_registers_bank");
#print "RESP:".&info_service_client::get_cr_regfile(ui=>"cr_info",name=>"MCHBAR_0_0_0_PCI",regfile_filter_str=>"iop_registers_bank");
#print "RESP:".&info_service_client::get_cr_fields(ui=>"cr_info",name=>"MCHBAR_0_0_0_PCI",regfile_filter_str=>"iop_registers_bank");
#print "RESP:".&info_service_client::get_cr_field_boundaries(ui=>"cr_info",field=>"MCHBAR",crname=>"MCHBAR_0_0_0_PCI",regfile_filter_str=>"iop_registers_bank");
#print "RESP:".&info_service_client::get_cr_address_by_name(ui=>"cr_info",name=>"LT_SMX_STATE",regfile_filter_str=>"LT_PATCH_FLAG");#fscp
#print "RESP:".&info_service_client::get_cr_address_by_name(ui=>"cr_info",name=>"MISC_CFG",regfile_filter_str=>"pma_regs_cbo0");#pmsb
#print "RESP:".&info_service_client::get_cr_properties_by_name(ui=>"cr_info",name=>"LT_SMX_STATE",regfile_filter_str=>"LT_PATCH_FLAG"ui=>"cr_info",name=>"MISC_CFG",regfile_filter_str=>"pma_regs_cbo0");#pmsb
#---FSCP
$val=&info_service_client::get_reg_properties_by_name(name=>"LT_SMX_STATE",regfile_filter_str=>"fscp");
print "LT_SMX_STATE:"."addr=>".$val->{"addr"}." ,type=>".$val->{"type"}." ,bar=>".$val->{"bar"}." ,device=>".$val->{"device"}." ,portid=>".$val->{"portid"}." ,function=>".$val->{"function"}." ,
              size=>".$val->{"size"}." , msr_address=>".$val->{"msr_address"}."\n";
#---PMSB
$val=&info_service_client::get_reg_properties_by_name(name=>"MISC_CFG",regfile_filter_str=>"pma_regs_cbo0");
print "MISC_CFG:"."addr=>".$val->{"addr"}." ,type=>".$val->{"type"}." ,bar=>".$val->{"bar"}." ,device=>".$val->{"device"}." ,portid=>".$val->{"portid"}." ,function=>".$val->{"function"}." ,
              size=>".$val->{"size"}." , msr_address=>".$val->{"msr_address"}."\n";
#iosf
$val=&info_service_client::get_reg_properties_by_name(name=>"MCHBAR_0_0_0_PCI",regfile_filter_str=>"iop_registers_bank");
print "MCHBAR_0_0_0_PCI"."addr=>".$val->{"addr"}." ,type=>".$val->{"type"}." ,bar=>".$val->{"bar"}." ,device=>".$val->{"device"}." ,portid=>".$val->{"portid"}." ,function=>".$val->{"function"}." ,
              size=>".$val->{"size"}." , msr_address=>".$val->{"msr_address"}."\n";
