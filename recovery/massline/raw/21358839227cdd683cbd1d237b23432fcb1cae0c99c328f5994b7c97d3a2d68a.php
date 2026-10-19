<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html><head>
	<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1" />
	<meta name="description" content="Register" />
	<meta name="keywords" content="PHP, MySQL, bulletin, board, free, open, source, smf, simple, machines, forum" />
	<script language="JavaScript" type="text/javascript" src="http://masslinemedia.com/smf/Themes/default/script.js"></script>
	<script language="JavaScript" type="text/javascript"><!--
		var smf_theme_url = "http://masslinemedia.com/smf/Themes/safgrey105";
		var smf_images_url = "http://masslinemedia.com/smf/Themes/safgrey105/images";
	// --></script>
	<title>Register</title>
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
							October 24, 2007, 05:35:39 pm<br />
                   <td class="headerdown" align="right" width="40%" style="padding-right: 8px;">
							<b>36558</b> Posts in <b>2351</b> Topics by <b>492</b> Members<br />
							Latest Member: <b> <a href="http://masslinemedia.com/smf/index.php?action=profile;u=2434">Cerimaskl</a></b>
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
<script language="JavaScript" type="text/javascript"><!--
	function agreesubmit(el)
	{
		document.creator.regSubmit.disabled = !el.checked;
	}
	function defaultagree()
	{
		if (!document.creator.regagree.checked)
		{
			alert("Please read/accept terms to submit form.");
			return false;
		}
		return true;
	}
// --></script>
<form action="http://masslinemedia.com/smf/index.php?action=register2" method="post" name="creator" onsubmit="return defaultagree();">
	<table border="0" width="100%" cellpadding="3" cellspacing="0" class="tborder">
		<tr class="titlebg">
			<td>Register - Required Information</td>
		</tr><tr class="windowbg">
			<td width="100%">
				<table cellpadding="3" cellspacing="0" border="0" width="100%">
					<tr>
						<td width="40%">
							<b>Choose username:</b>
							<div class="smalltext">Used only for identification by SMF. You can use special characters after logging in, by changing your displayed name in your profile.</div>
						</td>
						<td>
							<input type="text" name="user" size="20" maxlength="18" />
						</td>
					</tr><tr>
						<td width="40%">
							<b>Email:</b>
							<div class="smalltext">This must be a valid email address.</div>
						</td>
						<td>
							<input type="text" name="email" size="30" />
							<input type="checkbox" name="hideEmail" class="check" id="hideEmail" /> <label for="hideEmail">Hide email address from public?</label>
						</td>
					</tr><tr>
						<td width="40%">
							<b>Choose password:</b>
						</td>
						<td>
							<input type="password" name="passwrd1" size="30" />
						</td>
					</tr><tr>
						<td width="40%">
							<b>Verify password:</b>
						</td>
						<td>
							<input type="password" name="passwrd2" size="30" />
						</td>
					</tr>
				</table>
			</td>
		</tr>
	</table>
	<table width="100%" align="center" border="0" cellspacing="0" cellpadding="5" class="tborder" style="border-top: 0;">
		<tr>
			<td class="windowbg2" style="padding-top: 8px; padding-bottom: 8px;">
				You agree, through your use of this forum, that you will not post any material which is false, defamatory, inaccurate, abusive, vulgar, hateful, harassing, obscene, profane, sexually oriented, threatening, invasive of a person's privacy, adult material, or otherwise in violation of any International or United States Federal law. You also agree not to post any copyrighted material unless you own the copyright or you have written consent from the owner of the copyrighted material. Spam, flooding, advertisements, chain letters, pyramid schemes, and solicitations are also forbidden on this forum.<br />
<br />
Note that it is impossible for the staff or the owners of this forum to confirm the validity of posts. Please remember that we do not actively monitor the posted messages, and as such, are not responsible for the content contained within. We do not warrant the accuracy, completeness, or usefulness of any information presented. The posted messages express the views of the author, and not necessarily the views of this forum, its staff, its subsidiaries, or this forum's owner. Anyone who feels that a posted message is objectionable is encouraged to notify an administrator or moderator of this forum immediately. The staff and the owner of this forum reserve the right to remove objectionable content, within a reasonable time frame, if they determine that removal is necessary. This is a manual process, however, please realize that they may not be able to remove or edit particular messages immediately. This policy applies to member profile information as well.<br />
<br />
You remain solely responsible for the content of your posted messages. Furthermore, you agree to indemnify and hold harmless the owners of this forum, any related websites to this forum, its staff, and its subsidiaries. The owners of this forum also reserve the right to reveal your identity (or any other related information collected on this service) in the event of a formal complaint or legal action arising from any situation caused by your use of this forum.<br />
<br />
You have the ability, as you register, to choose your username. We advise that you keep the name appropriate. With this user account you are about to register, you agree to never give your password out to another person except an administrator, for your protection and for validity reasons. You also agree to NEVER use another person's account for any reason.  We also HIGHLY recommend you use a complex and unique password for your account, to prevent account theft.<br />
<br />
After you register and login to this forum, you will be able to fill out a detailed profile. It is your responsibility to present clean and accurate information. Any information the forum owner or staff determines to be inaccurate or vulgar in nature will be removed, with or without prior notice. Appropriate sanctions may be applicable.<br />
<br />
Please note that with each post, your IP address is recorded, in the event that you need to be banned from this forum or your ISP contacted. This will only happen in the event of a major violation of this agreement.<br />
<br />
Also note that the software places a cookie, a text file containing bits of information (such as your username and password), in your browser's cache. This is ONLY used to keep you logged in/out. The software does not collect or send any other form of information to your computer.
			</td>
		</tr><tr>
			<td align="center" class="windowbg2">
				<label for="regagree"><input type="checkbox" name="regagree" onclick="agreesubmit(this);" class="check" id="regagree" /> <b>I Agree</b></label>
			</td>
		</tr>
	</table>
	<br />
	<div align="center">
		<input type="submit" name="regSubmit" value="Register" />
	</div>
</form>
<script language="JavaScript" type="text/javascript">
	document.creator.regagree.checked = false;
	document.creator.regSubmit.disabled = true;
</script></td>
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