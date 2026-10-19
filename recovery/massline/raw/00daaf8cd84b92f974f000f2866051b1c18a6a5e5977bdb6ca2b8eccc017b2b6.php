<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html><head>
	<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1" />
	<meta name="description" content="Set Search Parameters" />
	<meta name="keywords" content="PHP, MySQL, bulletin, board, free, open, source, smf, simple, machines, forum" />
	<script language="JavaScript" type="text/javascript" src="http://masslinemedia.com/smf/Themes/default/script.js"></script>
	<script language="JavaScript" type="text/javascript"><!--
		var smf_theme_url = "http://masslinemedia.com/smf/Themes/safgrey105";
		var smf_images_url = "http://masslinemedia.com/smf/Themes/safgrey105/images";
	// --></script>
	<title>Set Search Parameters</title>
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
							Welcome, <b>Guest</b>. Please <a href="http://masslinemedia.com/smf/index.php?action=login">login</a> or <a href="http://masslinemedia.com/smf/index.php?action=register">register</a>.<br />Did you miss your <a href="http://masslinemedia.com/smf/index.php?action=activate">activation email?</a><br />
							April 17, 2009, 04:42:08 AM<br />
                   <td class="headerdown" align="right" width="40%" style="padding-right: 8px;">
							<b>44637</b> Posts in <b>3333</b> Topics by <b>8272</b> Members<br />
							Latest Member: <b> <a href="http://masslinemedia.com/smf/index.php?action=profile;u=11753">Joseph Giraud</a></b>
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
		function checkAll(onOff)
		{
			for (var i = 0; i < document.searchform.elements.length; i++)
			{
				if (document.searchform.elements[i].name.substr(0, 3) == "brd")
					document.searchform.elements[i].checked = onOff;
			}
		}
	// --></script>
	<form action="http://masslinemedia.com/smf/index.php?action=search2" method="post" name="searchform" id="searchform">
		<table width="80%" border="0" cellspacing="0" cellpadding="3" align="center">
			<tr>
				<td><span class="nav"><b><a href="http://masslinemedia.com/smf/index.php" class="nav">MASSLINE</a></b> &nbsp;|&nbsp; <b><a href="http://masslinemedia.com/smf/index.php?action=search" class="nav">Search</a></b></span></td>
			</tr>
		</table>

		<table width="80%" border="0" cellspacing="0" cellpadding="4" align="center" class="tborder">
			<tr class="titlebg">
				<td>Set Search Parameters</td>
			</tr><tr>
				<td class="windowbg">
					<input type="hidden" name="advanced" value="1" />
					<table cellpadding="1" cellspacing="3" border="0">
						<tr>
							<td>
								<b>Search for:</b>
							</td>
							<td></td>
							<td>
								<b>by user:</b>
							</td>
						</tr><tr>
							<td>
								<input type="text" name="search" size="40" />
							</td><td style="padding-right: 2ex;">
								<select name="searchtype">
									<option value="1" selected="selected">Match all words</option>
									<option value="2">Match any words</option>
								</select>
							</td><td>
								<input type="text" name="userspec" value="*" size="40" />
							</td>
						</tr><tr>
							<td style="padding-top: 2ex;" colspan="2"><b>Options:</b></td>
							<td style="padding-top: 2ex;"><b>Message age: </b></td>
						</tr><tr>
							<td colspan="2">
								<label for="show_complete"><input type="checkbox" name="show_complete" id="show_complete" value="1" class="check" /> Show results as messages</label><br />
								<label for="subject_only"><input type="checkbox" name="subject_only" id="subject_only" value="1" class="check" /> Topic subjects only</label>
							</td>
							<td>
								Between <input type="text" name="minage" value="0" size="5" maxlength="5" />&nbsp;and&nbsp;<input type="text" name="maxage" value="9999" size="5" maxlength="5" /> days.
							</td>
						</tr><tr>
							<td style="padding-top: 2ex;" colspan="2"><b>Search order:</b></td>
							<td></td>
						</tr><tr>
							<td colspan="2">
								<select name="sort">
									<option value="relevance|desc">Most relevant results first</option>
									<option value="numReplies|desc">Largest topics first</option>
									<option value="numReplies|asc">Smallest topics first</option>
									<option value="ID_MSG|desc">Most recent topics first</option>
									<option value="ID_MSG|asc">Oldest topics first</option>
								</select>
							</td>
							<td></td>
						</tr>
					</table>
					<br />
					<b>Choose a board to search in, or search all:</b><br />

					<table width="80%" border="0" cellpadding="1" cellspacing="0">
						<tr>
							<td width="50%"><span style="text-decoration: underline;">MASS LINE FORUMS</span>
							</td>
							<td width="50%">
								<label for="brd6" style="margin-left: 0ex;"><input type="checkbox" id="brd6" name="brd[6]" value="6" checked="checked" class="check" />
								Video Forum</label>
							</td>
						</tr>
						<tr>
							<td width="50%">
								<label for="brd1" style="margin-left: 0ex;"><input type="checkbox" id="brd1" name="brd[1]" value="1" checked="checked" class="check" />
								Mass Line Artist Discussion</label>
							</td>
							<td width="50%">
								<label for="brd7" style="margin-left: 0ex;"><input type="checkbox" id="brd7" name="brd[7]" value="7" checked="checked" class="check" />
								The Opium Den</label>
							</td>
						</tr>
						<tr>
							<td width="50%">
								<label for="brd2" style="margin-left: 0ex;"><input type="checkbox" id="brd2" name="brd[2]" value="2" checked="checked" class="check" />
								The Dialogue</label>
							</td>
							<td width="50%">
								<label for="brd5" style="margin-left: 0ex;"><input type="checkbox" id="brd5" name="brd[5]" value="5" checked="checked" class="check" />
								The Arena</label>
							</td>
						</tr>
						<tr>
							<td width="50%">
								<label for="brd3" style="margin-left: 0ex;"><input type="checkbox" id="brd3" name="brd[3]" value="3" checked="checked" class="check" />
								By Any Means</label>
							</td>
							<td width="50%"><span style="text-decoration: underline;">MASS LINE STREET TEAM</span>
							</td>
						</tr>
						<tr>
							<td width="50%">
								<label for="brd8" style="margin-left: 0ex;"><input type="checkbox" id="brd8" name="brd[8]" value="8" checked="checked" class="check" />
								The Review Section</label>
							</td>
							<td width="50%">
								<label for="brd4" style="margin-left: 0ex;"><input type="checkbox" id="brd4" name="brd[4]" value="4" checked="checked" class="check" />
								Mass Line Street Team</label>
							</td>
						</tr>
						<tr>
							<td width="50%">
								<label for="brd9" style="margin-left: 0ex;"><input type="checkbox" id="brd9" name="brd[9]" value="9" checked="checked" class="check" />
								The Business</label>
							</td>
						</tr>
					</table><br />
					<input type="checkbox" name="all" id="check_all" value="" checked="checked" onclick="invertAll(this, this.form, 'brd');" class="check" /><i> <label for="check_all">Check all</label></i><br />
					<br />

					<div style="padding: 2px;"><input type="submit" name="submit" value="Search" /></div>
				</td>
			</tr>
		</table>
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