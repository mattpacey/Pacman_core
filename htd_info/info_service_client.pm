#!/usr/intel/pkgs/perl/5.8.7/bin/perl 

package info_service_client;

#use strict;
$|++;
use IO::Socket;
use Getopt::Long qw(:config pass_through);
use warnings;
require Exporter;


# TODO : Are these exporter calls doing/buying anything?
our @ISA = qw(Exporter);

# Items to export into callers namespace by default. Note: do not export
# names by default without a very good reason. Use EXPORT_OK instead.
# Do not simply export all your public functions/methods/constants.

# This allows declaration	use info_service_client ':all';
# If you do not need this, moving things directly into @EXPORT or @EXPORT_OK
# will save memory.
our %EXPORT_TAGS = (
   'all' => [
      qw(

        )
   ]
);

our @EXPORT_OK = ( @{$EXPORT_TAGS{'all'}} );

our @EXPORT = qw(

);

our $VERSION = '0.01';

# Preloaded methods go here.
# TODO : Why is the path being overwritten?
BEGIN { $ENV{PATH} = $ENV{PATH}.':/usr/ucb:/bin'}
# TODO : These two methods don't seem to be used anywhere. Can they be removed?
sub process_spawn; # forward declaration
sub logmsg {print "$0 $$: @_ at ", scalar localtime, "\n"}

my($server,$QueueDbg,$QueueLength);
# perl -wc pacifiers
$info_service_client::server  = undef;
#$info_service_client::IPC_RMID   = 0;
#$info_service_client::MSG_EXCEPT = 20000;
$info_service_client::QueueDbg    = 0;
$info_service_client::QueueLength = 1000;



##
## Purpose    : Catchall for undefined functions: http://perldoc.perl.org/AutoLoader.html
##
## Algorithm  : Find function by traversing the schema tree (and check params)?
##              TODO: Expand this more.
##
## Syntax     : This shouldn't be called directly, it's called when the requested routine is not found.
##
## Return Code: Requested function if found. 
##
## Exit Codes : Kill process if the function is not found.
##
###########################################################################################
sub AUTOLOAD {
   my ( @rv )   = caller;
   my ( $file ) = $rv[1];
   $file =~ s/[A-z0-9_]+\///g;
   $file =~ s/^\///g;
   my ( $line ) = $rv[2];
   my $name = our $AUTOLOAD;
      my $fname = "";
      if ( $name =~ m/info_service_client::(\S+)/ ) {
         $fname = $1;
         }
      else {
         die( "ERROR: Undefined library call : $name , Expected token : info_service_client::(\\S+)..\n" );
         }
   #--------------------
   if(	!defined($info_service_client::server ) ){
     &info_service_client::init();
   };
   #-----------------------
   my %args = @_;
   #----Verify that all arguments  are valid----
   my $sock_arg_cmd = "";
   foreach my $arg ( keys %args ) {
       if ($arg eq "ui") { next;}
       $sock_arg_cmd = $sock_arg_cmd . "," . $arg . "=" . $args{$arg};
      }
   if(!defined($args{"ui"})){
     die( "ERROR: Missing \"ui\" argument at: $file line: $line.This argument define a INFO User interface name reference <ui>:<method>..\n" );
   };
   return &info_service_client::write( "NAME=" . $fname ."," . "ui=".$args{"ui"}.$sock_arg_cmd );
}
###########################################################################################
##
## Function   : get_reg_properties_by_name
##
## Purpose    : Get register properties in hash {TYPE BAR DEVICE FUNCTION PORTID SIZE MSR_ADDRESS AREA
##
##
## Syntax     : &parse_info_service_clientargs( @ARGV );
##
## Return Code: hash{TYPE BAR DEVICE FUNCTION PORTID SIZE MSR_ADDRESS AREA}
##
##
###########################################################################################
sub  get_reg_properties_by_name {
   my ( @rv )   = caller;
   my ( $file ) = $rv[1];
   $file =~ s/[A-z0-9_]+\///g;
   $file =~ s/^\///g;
   my ( $line ) = $rv[2];
   my $name = "get_reg_properties_by_name";
   my %args = @_;
   if(!defined($args{"name"})){
     die( "ERROR: Missing register name \"name\" argument at: $file line: $line.:get_reg_properties_by_name(name=><reg_name>) ..\n" );
   };
   $regfile_str="";
   if(defined($args{"regfile_filter_str"})){
    $regfile_str=$args{"regfile_filter_str"};
   };
   #-------------------------
   
   $cr_addr=&info_service_client::get_cr_address_by_name(ui=>"cr_info",name=>$args{"name"},regfile_filter_str=>$regfile_str);
   #print "type:".&info_service_client::has_cr_property_by_name(ui=>"cr_info",name=>$args{"name"},regfile_filter_str=>$regfile_str,property_str=>"type")."\n";
   #print "bar:".&info_service_client::has_cr_property_by_name(ui=>"cr_info",name=>$args{"name"},regfile_filter_str=>$regfile_str,property_str=>"bar")."\n";
   #print "device:".&info_service_client::has_cr_property_by_name(ui=>"cr_info",name=>$args{"name"},regfile_filter_str=>$regfile_str,property_str=>"device")."\n";
   #print "function:".&info_service_client::has_cr_property_by_name(ui=>"cr_info",name=>$args{"name"},regfile_filter_str=>$regfile_str,property_str=>"function")."\n";
   #print "portid:".&info_service_client::has_cr_property_by_name(ui=>"cr_info",name=>$args{"name"},regfile_filter_str=>$regfile_str,property_str=>"portid")."\n";
   #print "size:".&info_service_client::has_cr_property_by_name(ui=>"cr_info",name=>$args{"name"},regfile_filter_str=>$regfile_str,property_str=>"size")."\n";

   if(&info_service_client::has_cr_property_by_name(ui=>"cr_info",name=>$args{"name"},regfile_filter_str=>$regfile_str,property_str=>"type")){
    $type=&info_service_client::get_cr_property_by_name(ui=>"cr_info",name=>$args{"name"},regfile_filter_str=>$regfile_str,property_str=>"type");
   } else {
    $type=undef;
   }

   if(&info_service_client::has_cr_property_by_name(ui=>"cr_info",name=>$args{"name"},regfile_filter_str=>$regfile_str,property_str=>"bar")){
    $bar=&info_service_client::get_cr_property_by_name(ui=>"cr_info",name=>$args{"name"},regfile_filter_str=>$regfile_str,property_str=>"type");
   } else {
    $bar=undef;
   }
   if(&info_service_client::has_cr_property_by_name(ui=>"cr_info",name=>$args{"name"},regfile_filter_str=>$regfile_str,property_str=>"device")){
    $device=&info_service_client::get_cr_property_by_name(ui=>"cr_info",name=>$args{"name"},regfile_filter_str=>$regfile_str,property_str=>"device");
   } else {
    $device=undef;
   }
   if(&info_service_client::has_cr_property_by_name(ui=>"cr_info",name=>$args{"name"},regfile_filter_str=>$regfile_str,property_str=>"function")){
    $function=&info_service_client::get_cr_property_by_name(ui=>"cr_info",name=>$args{"name"},regfile_filter_str=>$regfile_str,property_str=>"function");
   } else {
    $function=undef;
   }
   if(&info_service_client::has_cr_property_by_name(ui=>"cr_info",name=>$args{"name"},regfile_filter_str=>$regfile_str,property_str=>"portid")){
    $portid=&info_service_client::get_cr_property_by_name(ui=>"cr_info",name=>$args{"name"},regfile_filter_str=>$regfile_str,property_str=>"portid");
   } else {
    $portid=undef;
   }
   if(&info_service_client::has_cr_property_by_name(ui=>"cr_info",name=>$args{"name"},regfile_filter_str=>$regfile_str,property_str=>"size")){
    $size=&info_service_client::get_cr_property_by_name(ui=>"cr_info",name=>$args{"name"},regfile_filter_str=>$regfile_str,property_str=>"size");
   } else {
    $size=undef;
   }
   if(&info_service_client::has_cr_property_by_name(ui=>"cr_info",name=>$args{"name"},regfile_filter_str=>$regfile_str,property_str=>"msr_address")){
    $msr_address=&info_service_client::get_cr_property_by_name(ui=>"cr_info",name=>$args{"name"},regfile_filter_str=>$regfile_str,property_str=>"msr_address");
   } else {
    $msr_address=undef;
   }
   
   return {"addr"=>$cr_addr,"type"=>$type,"bar"=>$bar,"device"=>$device,"portid"=>$portid,"function"=>$function,"size"=>$size,"msr_address"=>$msr_address};
}
###########################################################################################
##
## Function   : parse_info_service_clientargs
##
## Purpose    : Parse the command line arguments
##
## Algorithm  :
##
## Syntax     : &parse_info_service_clientargs( @ARGV );
##
## Return Code: 1 - success
##
## Exit Codes : none
##
###########################################################################################
sub parse_info_service_clientargs {
   for ( my $i = 0; $i < $#ARGV; $i++ ) {
      if ( $ARGV[$i] =~ m/-(\S+)/ ) {
         my $argName = $1;
         my $argVal  = "";
         for ( my $j = $i + 1; ( $j <= $#ARGV && $ARGV[$j] !~ m/-\S+/ ); $j++ ) {
            $argVal = $argVal . $ARGV[$j];
            }
         $info_service_client::Args{$argName} = $argVal;
         print "***ARGS: $argName=$info_service_client::Args{$argName}  \n";
         }

      }

   return 1;
   }

###########################################################################################
##
## Function   : end
##
## Purpose    : The VPI script has completed, close the server
##
## Algorithm  : TODO : Can this just be rolled up into info_service_clientEND?
##
## Syntax     : &info_service_client::info_service_clientend();
##
## Return Code: none
##
## Exit Codes : none
##
###########################################################################################
sub end {
   print $info_service_client::server "HTD_CLOSE_SERVER";
   sleep(10);
   $info_service_client::server->flush;
   $info_service_client::server->close;
   if(-e $info_service_client::socket_file) {unlink($info_service_client::socket_file);}
 }

###########################################################################################
##
## Function   : init
##
## Purpose    : Prepare INFO server server to listen for calls from INFO client scripts.
##
## Algorithm  : Parse args (error if something is missing), start server. 
##
## Syntax     : &info_service_client::init(); 
##
## Return Code: none
##
## Exit Codes : Exit if server arguments are not provided.
##
###########################################################################################
sub init {
   use Cwd 'abs_path';
   use File::Basename;
   #$ENV{INFO_CFG}=$ENV{PROJ_TOOLS}."/htd/latest/cdk-x0/project/cnl/htd_te_proj/TE_cfg.xml";
   #&info_service_client::parse_info_service_clientargs();
   
   $info_service_client::current_path=__FILE__;
   $info_service_client::current_path=~s/[A-z0-9_\.]+$//;   
   $info_service_client::tecfg="";
   if(!defined($info_service_client::Args{"infocfg"})) {
     if(!defined($ENV{"HTD_TE_CFG_REL"})){
       die "\nMissing INFO configuration file specification: by CMD -infocfg <path> or by ENV[HTD_TE_CFG_REL] \n";
     }else{
       $info_service_client::tecfg=$ENV{"HTD_TE_CFG_REL"};
     };
   } else {
     $info_service_client::tecfg=$info_service_client::Args{"infocfg"};
   };
   #------------------------------------------------------
   $info_service_client::socket_file="InfoSocket_".$ENV{ USER }."_1";
   my $sock_file_index=1;
   while(-e $info_service_client::socket_file) {
     $sock_file_index+=1;
     $info_service_client::socket_file="InfoSocket_".$ENV{ USER }."_".$sock_file_index;
   }
   #---------------------------------------------------------
   $info_service_client::info_cmd=$info_service_client::current_path."info_service.py -tecfg ".$info_service_client::tecfg." -socket ".$info_service_client::socket_file;
   print "Executing the INFO server: $info_service_client::info_cmd ...";
   if(fork) {
      print "********Connecting Client...\n";
      while(1)
      {
          print "Waiting Server boot on socket file(".$info_service_client::socket_file.")\n";
          sleep(4);
	  if(-e $info_service_client::socket_file) { last;}
      }  
      $info_service_client::server = IO::Socket::UNIX->new( Peer => $info_service_client::socket_file, Type => SOCK_STREAM ) or die "ERROR:  INFO client:socket: $!\n";
      print "**************INFO Connection Active on socket: $info_service_client::socket_file ******************\n";
      alarm(7200);
      return
   }else{
    if(defined($info_service_client::Args{"noserver"}) && $info_service_client::Args{"noserver"}) {
      print "NORUN INFO server mode, pls run cmd manually: $info_service_client::info_cmd \n";
    }else {
     exec($info_service_client::info_cmd)   or print STDERR "couldn't exec $info_service_client::info_cmd: $!";
    }
    #------------------------
   }
}

###########################################################################################
##
## Function   : info_service_clientread 
##
## Purpose    : TODO : This doesn't seem to be used, can it be deleted?
##
## Algorithm  :
##
## Syntax     : 
##
## Return Code: 
##
## Exit Codes : 
##
###########################################################################################
sub read {
   my ( $aknowledge ) = @_;
   if ( !defined( $aknowledge ) ) {$aknowledge = "1";}
   #print "VPI: reading  \n";
   my $data;
   $info_service_client::server->recv( $data, $info_service_client::QueueLength ) or die "VPI: info_service_clientread: $! \n";
   #---Aknowledgemnet -----
   print $info_service_client::server $aknowledge;
   print "sock reading done: $data \n--------------------------------------\n";
   return $data;
   }

###########################################################################################
##
## Function   : info_service_clientwrite 
##
## Purpose    : Method for passing info (functions to the VPI server).
##
## Algorithm  : Send function call to server, read response.
##
## Syntax     : &info_service_client::info_service_clientwrite( "NAME:" . $condition_name . ":FUNC:" . $func_name );
##
## Return Code: $data as returned by function call.
##
## Exit Codes : none
##
###########################################################################################
sub write {
   my ( $msg ) = @_;
   print $info_service_client::server $msg;
   $info_service_client::server->flush;
   my $data;
   $info_service_client::server->recv( $data, $info_service_client::QueueLength ) or die "INFO: info_service_clientWrite: $! $msg\n";#Get response "OK"
   $info_service_client::server->recv( $data, $info_service_client::QueueLength ) or die "INFO: info_service_clientWrite: $! $msg\n";#Get real response
   return $data;
   }


###########################################################################################
##
## Function   : Timerout 
##
## Purpose    : TODO : I don't see this used anywhere, can it be removed?
##
## Algorithm  :
##
## Syntax     : 
##
## Return Code: 
##
## Exit Codes : 
##
###########################################################################################

$SIG{ALRM} =sub { 
  print ": VPI timed out\n";
  &info_service_client::info_service_clientend();
   print "\n*********** VPI $0 Ended ************ \n";
};
END {
    # cleanup
    print "Closing service connection...\n";
    &info_service_client::end();
}
#=-=#=-=#=-=#=-=#=-=#=-=#=-=#=-=#=-=#=-=#=-=#=-=#
#       End of Project Specific Functions       #
#=-=#=-=#=-=#=-=#=-=#=-=#=-=#=-=#=-=#=-=#=-=#=-=#
# return a good status to require

1;
__END__
