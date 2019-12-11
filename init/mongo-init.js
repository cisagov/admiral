db.createUser({
  user: "logger",
  pwd: "example",
  roles: [
    {
      role: "readWrite",
      db: "certs"
    }
  ]
});
