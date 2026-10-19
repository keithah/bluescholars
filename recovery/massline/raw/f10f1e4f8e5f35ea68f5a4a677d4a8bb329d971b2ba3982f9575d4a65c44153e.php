	<html>
	<head>
	<script language="JavaScript">
	function firstFocus()
	{
		if (document.forms.length > 0) {
			var TForm = document.forms[0];
			for (i=0;i<TForm.length;i++) {
				if ((TForm.elements[i].type=="text")|| 
				    (TForm.elements[i].type=="textarea")|| 
					(TForm.elements[i].type.toString().charAt(0)=="s")) {
					document.forms[0].elements[i].focus();
					break;
				}
			}
		}
	}
	</script>
	<title>MassLine Calendar Login Page</title>
	<link rel="stylesheet" type="text/css" href="css/adminpgs.css">
	</head>
	<body onLoad="firstFocus()">
	<span class="login_header">MassLine Calendar Login</span>
	<br><img src="images/clear.gif" width="1" height="5"><br>
	
	<table>
	<form action="/cal/login.php?action=login&month=0&year=0" method="post">
			<tr>
				<td nowrap valign="top" align="right" nowrap>
				<span class="login_label">Username</span></td>
				<td><input type="text" name="username" size="29" maxlength="15"></td>
			</tr>
			<tr>
				<td nowrap valign="top" align="right" nowrap>
				<span class="login_label">Password</span></td>
				<td><input type="password" name="password" size="29" maxlength="15"></td>
			</tr>
			<tr><td colspan="2" align="right"><input type="submit" value="Login"><td><tr>
	</form>
	</table>

	</body></html>
