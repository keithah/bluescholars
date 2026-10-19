<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html><head>
	<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1" />
	<meta name="description" content="MASSLINE Password Reminder" />
	<meta name="keywords" content="PHP, MySQL, bulletin, board, free, open, source, smf, simple, machines, forum" />
	<script language="JavaScript" type="text/javascript" src="http://masslinemedia.com/smf/Themes/default/script.js"></script>
	<script language="JavaScript" type="text/javascript"><!--
		var smf_theme_url = "http://masslinemedia.com/smf/Themes/safgrey105";
		var smf_images_url = "http://masslinemedia.com/smf/Themes/safgrey105/images";
	// --></script>
	<title>MASSLINE Password Reminder</title>
	<link rel="stylesheet" type="text/css" href="http://masslinemedia.com/smf/Themes/safgrey105/style.css" />
	<link rel="help" href="http://masslinemedia.com/smf/index.php?action=help" target="_blank" />
	<link rel="search" href="http://masslinemedia.com/smf/index.php?action=search" />
	<link rel="contents" href="http://masslinemedia.com/smf/index.php" />

	<script language="JavaScript" type="text/javascript"><!--
		var current_header = false;

		function shrinkHeader(mode)
		{
			document.cookie = "upshrink=" + (mode ? 1 : 0);
			document.getElementById("upshrink").src = smf_images_url + (mode ? "/upshrink2.gif" : "/upshrink.gif");

			document.getElementById("upshrinkHeader").style.display = mode ? "none" : "";

			current_header = mode;
		}
	// --></script>
</head>
<body>
        <center>
        <table class="maintable" cellspacing="0" cellpadding="0" border="0" align="center" width="760
        ">
               <tr>
                   <td class="header">&nbsp;

                   </td>
               </tr>
               <tr>
                   <td>
        <table width="100%" cellspacing="0" cellpadding="0" border="0">
               <tr>
        <td class="headerdown" align="left" width="60%">
							Welcome, <b>Guest</b>. Please <a href="http://masslinemedia.com/smf/index.php?action=login">login</a> or <a href="http://masslinemedia.com/smf/index.php?action=register">register</a>.<br />
							August 01, 2009, 09:11:31 PM<br />
                   <td class="headerdown" align="right" width="40%" style="padding-right: 8px;">
							<b>44627</b> Posts in <b>3298</b> Topics by <b>939</b> Members<br />
							Latest Member: <b> <a href="http://masslinemedia.com/smf/index.php?action=profile;u=13965">Nikki_Hot_Girl</a></b>
	           </td>
                   </tr>
                   </table>
                   </td>
               </tr>
               <tr>
                   <td class="bodytd">
        <div align="center" style="padding-top: 4px;">
                
				<a href="http://masslinemedia.com/smf/index.php"><img src="http://masslinemedia.com/smf/Themes/safgrey105/images/english/home.gif" alt="Home" style="margin: 2px 0;" border="0" /></a> 
				<a href="http://masslinemedia.com/smf/index.php?action=help" target="_blank"><img src="http://masslinemedia.com/smf/Themes/safgrey105/images/english/help.gif" alt="Help" style="margin: 2px 0;" border="0" /></a> 
				<a href="http://masslinemedia.com/smf/index.php?action=search"><img src="http://masslinemedia.com/smf/Themes/safgrey105/images/english/search.gif" alt="Search" style="margin: 2px 0;" border="0" /></a> 
				<a href="http://masslinemedia.com/smf/index.php?action=calendar"><img src="http://masslinemedia.com/smf/Themes/safgrey105/images/english/calendar.gif" alt="Calendar" style="margin: 2px 0;" border="0" /></a> 
				<a href="http://masslinemedia.com/smf/index.php?action=login"><img src="http://masslinemedia.com/smf/Themes/safgrey105/images/english/login.gif" alt="Login" style="margin: 2px 0;" border="0" /></a> 
				<a href="http://masslinemedia.com/smf/index.php?action=register"><img src="http://masslinemedia.com/smf/Themes/safgrey105/images/english/register.gif" alt="Register" style="margin: 2px 0;" border="0" /></a>
        </div>
	<table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
		<td>
	<br />
	<form action="http://masslinemedia.com/smf/index.php?action=reminder;sa=mail" method="post">
		<table border="0" width="400" cellspacing="0" cellpadding="4" align="center" class="tborder">
			<tr class="titlebg">
				<td colspan="2">
					Password reminder
				</td>
			</tr><tr class="windowbg">
				<td colspan="2">Username/Email: <input type="text" name="user" size="30" /> <input type="submit" value="Send" /></td>
			</tr><tr class="windowbg">
				<td align="center"><input type="radio" name="searchtype" value="usearch" checked="checked" id="usearch" class="check" /> <label for="usearch">by User</label></td>
				<td align="center"><input type="radio" name="searchtype" value="esearch" id="esearch" class="check" /> <label for="esearch">by Email</label></td>
			</tr><tr class="windowbg">
				<td colspan="2" align="center"><input type="checkbox" name="sa" value="secret" id="secret" class="check" /> <label for="secret">Ask me my question</label></td>
			</tr><tr class="windowbg">
				<td colspan="2" align="center" class="smalltext">You can't retrieve your password, but you can set a new one by following a link sent to you by email.  You also have the option of setting a new password by answering your secret question.</td>
			</tr>
		</table>
		<input type="hidden" name="sc" value="f82a4027d8476aa82c11fa1b8dbea9c9" />
	</form></td>
	</tr></table><br />
        </td>
        </tr>
        <tr>
        <td class="footer">
		<table cellspacing="0" cellpadding="3" border="0" align="center" width="100%">
			<tr>
				<td width="28%" valign="middle" align="right">
					<a href="http://www.mysql.com/" target="_blank"><img id="powered-mysql" src="http://masslinemedia.com/smf/Themes/safgrey105/images/powered-mysql.gif" alt="Powered by MySQL" width="30" height="18" style="margin: 5px 16px;" border="0" /></a>
					<a href="http://www.php.net/" target="_blank"><img id="powered-php" src="http://masslinemedia.com/smf/Themes/safgrey105/images/powered-php.gif" alt="Powered by PHP" width="30" height="18" style="margin: 5px 16px;" border="0" /></a>
				</td>
				<td valign="middle" align="center" style="white-space: nowrap;" class="copyright">
					
		<span class="smalltext" style="display: inline; visibility: visible; font-family: Verdana, Arial, sans-serif;">MASSLINE | Powered by <a href="http://www.simplemachines.org/" title="Simple Machines Forum" target="_blank">SMF 1.0.10</a>.<br />
&copy; 2005, <a href="http://www.simplemachines.org/about/copyright.php" title="Free Forum Software" target="_blank">Simple Machines LLC</a>. All Rights Reserved.
		</span>
				</td>
				<td width="28%" valign="middle" align="left">
					<a href="http://validator.w3.org/check/referer" target="_blank"><img id="valid-xhtml10" src="http://masslinemedia.com/smf/Themes/safgrey105/images/valid-xhtml10.gif" alt="Valid XHTML 1.0!" width="30" height="18" style="margin: 5px 16px;" border="0" /></a>
					<a href="http://jigsaw.w3.org/css-validator/check/referer" target="_blank"><img id="valid-css" src="http://masslinemedia.com/smf/Themes/safgrey105/images/valid-css.gif" alt="Valid CSS!" width="30" height="18" style="margin: 5px 16px;" border="0" /></a>
				</td>
			</tr>
		</table>
        </td>
        </tr>

        </table>
        </center>
        </body>
</html>