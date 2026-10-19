<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html><head>
	<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1" />
	<meta name="description" content="Login" />
	<meta name="keywords" content="PHP, MySQL, bulletin, board, free, open, source, smf, simple, machines, forum" />
	<script language="JavaScript" type="text/javascript" src="http://masslinemedia.com/smf/Themes/default/script.js"></script>
	<script language="JavaScript" type="text/javascript"><!--
		var smf_theme_url = "http://masslinemedia.com/smf/Themes/safgrey105";
		var smf_images_url = "http://masslinemedia.com/smf/Themes/safgrey105/images";
	// --></script>
	<title>Login</title>
	<link rel="stylesheet" type="text/css" href="http://masslinemedia.com/smf/Themes/safgrey105/style.css" />
	<link rel="help" href="http://masslinemedia.com/smf/index.php?action=help" target="_blank" />
	<link rel="search" href="http://masslinemedia.com/smf/index.php?action=search" />
	<link rel="contents" href="http://masslinemedia.com/smf/index.php" />
	<link rel="prev" href="http://masslinemedia.com/smf/index.php?action=;topic=3870.0;prev_next=prev" />
	<link rel="next" href="http://masslinemedia.com/smf/index.php?action=;topic=3870.0;prev_next=next" />
	<link rel="index" href="http://masslinemedia.com/smf/index.php?action=;board=2.0" />

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
							January 04, 2010, 08:33:00 PM<br />
                   <td class="headerdown" align="right" width="40%" style="padding-right: 8px;">
							<b>44644</b> Posts in <b>3306</b> Topics by <b>3710</b> Members<br />
							Latest Member: <b> <a href="http://masslinemedia.com/smf/index.php?action=profile;u=16736">Elderipleally</a></b>
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
		<form action="http://masslinemedia.com/smf/index.php?action=login2" method="post" name="frmLogin">
			<table border="0" cellspacing="0" cellpadding="3" class="tborder" align="center">
				<tr class="titlebg">
					<td>Warning!</td>
				</tr><tr>
					<td class="windowbg" style="padding-top: 2ex; padding-bottom: 2ex;">
						Only registered members are allowed to access this section.<br />
						Please login below or <a href="http://masslinemedia.com/smf/index.php?action=register">register an account</a> with MASSLINE.
					</td>
				</tr><tr class="titlebg">
					<td><img src="http://masslinemedia.com/smf/Themes/safgrey105/images/icons/login_sm.gif" alt="" align="top" /> Login</td>
				</tr><tr>
					<td class="windowbg">
						<table border="0" cellpadding="3" cellspacing="0" align="center">
							<tr>
								<td align="right"><b>Username:</b></td>
								<td><input type="text" name="user" size="20" /></td>
							</tr><tr>
								<td align="right"><b>Password:</b></td>
								<td><input type="password" name="passwrd" size="20" /></td>
							</tr><tr>
								<td align="right"><b>Minutes to stay logged in:</b></td>
								<td><input type="text" name="cookielength" size="4" maxlength="4" value="60" /></td>
							</tr><tr>
								<td align="right"><b>Always stay logged in:</b></td>
								<td><input type="checkbox" name="cookieneverexp" class="check" onclick="document.frmLogin.cookielength.disabled = this.checked;" /></td>
							</tr><tr>
								<td align="center" colspan="2"><input type="submit" value="Login" style="margin-top: 2ex;" /></td>
							</tr><tr>
								<td align="center" colspan="2" class="smalltext"><a href="http://masslinemedia.com/smf/index.php?action=reminder">Forgot your password?</a><br /><br /></td>
							</tr>
						</table>
					</td>
				</tr>
			</table>
		</form>
		<script language="JavaScript" type="text/javascript"><!--
			document.frmLogin.user.focus();
		// --></script></td>
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