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
                        <td><a href="index.php?month=2&year=2007&PHPSESSID=5d0837ce406d0ee09492681fec60d4b4">
<img src="images/leftArrow.gif" border="0"></a> <a href="index.php?month=4&year=2007&PHPSESSID=5d0837ce406d0ee09492681fec60d4b4"><img src="images/rightArrow.gif" border="0"></a>                          <span class="date_header">&nbsp;
                          March                          &nbsp;
                          2007                          </span> </td>
                        <!-- form tags must be outside of <td> tags -->
                        <form name="monthYear"><input type="hidden" name="PHPSESSID" value="5d0837ce406d0ee09492681fec60d4b4" />
                          <td align="right">
<select name="month">
	<option value="1">January</option>
	<option value="2">February</option>
	<option value="3" selected>March</option>
	<option value="4">April</option>
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
                        <td colspan="2" bgcolor="#000000"><table cellpadding="1" cellspacing="1" border="0">
<tr>
	<td class="column_header">&nbsp;Sun</td>
	<td class="column_header">&nbsp;Mon</td>
	<td class="column_header">&nbsp;Tue</td>
	<td class="column_header">&nbsp;Wed</td>
	<td class="column_header">&nbsp;Thur</td>
	<td class="column_header">&nbsp;Fri</td>
	<td class="column_header">&nbsp;Sat</td>
</tr>

<tr>
	<td class="empty_day_cell" valign="top">&nbsp;</td>
	<td class="empty_day_cell" valign="top">&nbsp;</td>
	<td class="empty_day_cell" valign="top">&nbsp;</td>
	<td class="empty_day_cell" valign="top">&nbsp;</td>
	<td class="day_cell" valign="top"><span class="day_number">1</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">2</span><br><span class="title_txt">-<a href="javascript:openPosting(65)">Gabriel Teodros Live In Store Perform...</a></span><br><span class="title_txt">-<a href="javascript:openPosting(66)">Common Market at Edmmonds Community C...</a></span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">3</span><br><span class="title_txt">-<a href="javascript:openPosting(64)">Lyrics Born, The Coup at Neumo's</a></span><div align="right" class="time_str">(8:00AM - - -)&nbsp;</div><span class="title_txt">-<a href="javascript:openPosting(67)">Gabriel Teodros at The High Dive</a></span><br></td>
</tr>

<tr>
	<td class="day_cell" valign="top"><span class="day_number">4</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">5</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">6</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">7</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">8</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">9</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">10</span><br></td>
</tr>

<tr>
	<td class="day_cell" valign="top"><span class="day_number">11</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">12</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">13</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">14</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">15</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">16</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">17</span><br></td>
</tr>

<tr>
	<td class="day_cell" valign="top"><span class="day_number">18</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">19</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">20</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">21</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">22</span><br></td>
	<td class="today_cell" valign="top"><span class="day_number">23</span><br><span class="title_txt">-<a href="javascript:openPosting(68)">Blue Scholars at Northshore PAC</a></span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">24</span><br></td>
</tr>

<tr>
	<td class="day_cell" valign="top"><span class="day_number">25</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">26</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">27</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">28</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">29</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">30</span><br></td>
	<td class="day_cell" valign="top"><span class="day_number">31</span><br></td>
</tr>

</table>

 </td>
                      </tr>
                      <tr>
                        <td colspan="2" align="center">
						                        </td>
                      </tr>
                    </table>
</body>
</html>
