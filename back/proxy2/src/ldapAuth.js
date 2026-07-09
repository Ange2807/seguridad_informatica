const ldap = require("ldapjs");

// Intenta hacer bind en LDAP con las credenciales del usuario.
function bindAsUser(username, password) {
  return new Promise((resolve, reject) => {
    const client = ldap.createClient({ url: process.env.LDAP_URL });
    client.on("error", reject);
    const dn = `uid=${username},ou=people,${process.env.LDAP_BASE_DN}`;
    client.bind(dn, password, (err) => {
      client.unbind();
      if (err) return reject(err);
      resolve();
    });
  });
}

// Busca el grupo LDAP del usuario y devuelve su cn como rol.
function findRole(username) {
  return new Promise((resolve, reject) => {
    const client = ldap.createClient({ url: process.env.LDAP_URL });
    client.on("error", reject);
    client.bind(process.env.LDAP_ADMIN_DN, process.env.LDAP_ADMIN_PASSWORD, (bindErr) => {
      if (bindErr) {
        client.unbind();
        return reject(bindErr);
      }
      const base = `ou=groups,${process.env.LDAP_BASE_DN}`;
      const opts = {
        filter: `(member=uid=${username},ou=people,${process.env.LDAP_BASE_DN})`,
        scope: "sub",
        attributes: ["cn"],
      };
      let role = null;
      client.search(base, opts, (searchErr, result) => {
        if (searchErr) {
          client.unbind();
          return reject(searchErr);
        }
        result.on("searchEntry", (entry) => {
          const cnAttr = entry.pojo.attributes.find((attr) => attr.type === "cn");
          role = cnAttr ? cnAttr.values[0] : null;
        });
        result.on("error", (err) => {
          client.unbind();
          reject(err);
        });
        result.on("end", () => {
          client.unbind();
          resolve(role);
        });
      });
    });
  });
}

module.exports = { bindAsUser, findRole };
