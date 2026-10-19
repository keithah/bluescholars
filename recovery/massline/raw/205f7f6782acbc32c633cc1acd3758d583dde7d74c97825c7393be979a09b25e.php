<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<title>MASS LINE MEDIA</title>
	<script language="JavaScript">
	function submitMonthYear() {
		document.monthYear.method = "post";
		document.monthYear.action = "index.php?month=" + document.monthYear.month.value + "&year=" + document.monthYear.year.value;
		document.monthYear.submit();
	}

	function postMessage(day, month, year) {
		eval("page" + day + " = window.open('eventform.php?d=" + day + "&m=" + month + "&y=" + year + "', 'postScreen', 'toolbar=0,scrollbars=1,location=0,statusbar=0,menubar=0,resizable=1,width=340,height=475');");
	}

	function openPosting(pId) {
		eval("page" + pId + " = window.open('eventdisplay.php?id=" + pId + "', 'mssgDisplay', 'toolbar=0,scrollbars=1,location=0,statusbar=0,menubar=0,resizable=1,width=340,height=400');");
	}
	
	function loginPop(month, year) {
		eval("logpage = window.open('login.php?month=" + month + "&year=" + year + "', 'mssgDisplay', 'toolbar=0,scrollbars=1,location=0,statusbar=0,menubar=0,resizable=1,width=340,height=400');");
	}
	</script>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<style type="text/css">

<!--



.body1, .body1q {  line-height: 16px; }

.search_field {width: 295px; font-family: Verdana, Helvetica, sans-serif; font-size: 10px}

.edit_field {width: 150px; font-family: Verdana, Helvetica, sans-serif; font-size: 10px}

.ta_field { height: 150px; width: 400px; font-family: Verdana, Helvetica, sans-serif; font-size: 10px}



.edit_field, .ta_field, .search_field {

	border-left-color:#000000;

	border-top-color:#000000;

	border-right-color:#000000;

	border-bottom-color:#000000;

	color: #333333;

	border: 1 solid; }



A:link{color:#333300; font-family:verdana;text-decoration:none} 

A:visited{color:#333300; font-family:verdana;text-decoration:none};

A:hover{color:#FF3300} 
.style64 {
	font-family: Arial, Helvetica, sans-serif;
	font-weight: bold;
	color: #333300;
}
.style65 {
	color: #333300;
	font-family: Arial, Helvetica, sans-serif;
}
.style66 {font-size: 11px}
.style69 {font-size: 1.5px}
.style71 {font-size: 11px; color: #333300; }
.style72 {
	font-family: Verdana, Arial, Helvetica, sans-serif;
	font-size: 11px;
	color: #333300;
}
.style73 {
	font-family: Verdana, Helvetica, sans-serif;
	font-size: 11px;
	color: #333300;
}

-->

</style>
<link rel="stylesheet" type="text/css" href="css/default.css">
</head>
<body topmargin="0">
                    <table cellpadding="0" cellspacing="0" border="0" align="center">
                      <tr>
                        <td><a href="index.php?month=3&year=2007&PHPSESSID=5d0837ce406d0ee09492681fec60d4b4">
<img src="images/leftArrow.gif" border="0"></a> <a href="index.php?month=5&year=2007&PHPSESSID=5d0837ce406d0ee09492681fec60d4b4"><img src="images/rightArrow.gif" border="0"></a>                          <span class="date_header">&nbsp;
                          April                          &nbsp;
                          2007                          </span> </td>
                        <!-- form tags must be outside of <td> tags -->
                        <form name="monthYear"><input type="hidden" name="PHPSESSID" value="5d0837ce406d0ee09492681fec60d4b4" />
                          <td align="right">
<select name="month">
	<option value="1">January</option>
	<option value="2">February</option>
	<option value="3">March</option>
	<option value="4" selected>April</option>
	<option value="5">May</option>
	<option value="6">June</option>
	<option value="7">July</option>
	<option value="8">August</option>
	<option value="9">September</option>
	<option value="10">October</option>
	<option value="11">November</option>
	<option value="12">December</option>
</select>

<select name="year">
	<option value="2004">2004</option>
	<option value="2005">2005</option>
	<option value="2006">2006</option>
	<option value="2007" selected>2007</option>
	<option value="2008">2008</option>
	<option value="2009">2009</option>
	<option value="2010">2010</option>
</select>

                            <input type="button" value="GO" onClick="submitMonthYear()">
                          </td>
                        </form>
                      </tr>
                      <tr>
                        <td colspan="2" bgcolor="#000000">User 'massline_mysql' has exceeded the 'max_questions' resource (current value: 50000)