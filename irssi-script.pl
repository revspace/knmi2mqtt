$_{target} =~ '^#revspace|^[^#+&]' or return;

sub sensor {
    my ($topic) = @_;
    my $pid = open my $pipe, '-|', qw(timeout 1 mqtt-simple -1 -h mosquitto.space.revspace.nl -s), $topic;
    return (split " ", readline $pipe)[0] + 0;
}

sub text {
    my ($topic) = @_;
    my $pid = open my $pipe, '-|', qw(timeout 1 mqtt-simple -1 -h mosquitto.space.revspace.nl -s), $topic;
    my $value = readline $pipe;
    chomp $value;
    return $value;
}

sub tijd {
    my ($topic) = @_;

    use DateTime::Format::ISO8601;
    my $dt = DateTime::Format::ISO8601->parse_datetime(text($topic));
    return $dt->strftime("%Y-%m-%d %H:%M");
}

sub station {
    my ($id) = @_;

    return sprintf "%s: %s °C op 2 meter, %s °C op 10 cm, %s% RH \cC14(gemeten op %s)",
        text(sprintf "revspace/sensors/knmi/%s/stationname", $id),
        sensor(sprintf "revspace/sensors/knmi/%s/temperature-2m", $id),
        sensor(sprintf "revspace/sensors/knmi/%s/temperature-10cm", $id),
        sensor(sprintf "revspace/sensors/knmi/%s/humidity", $id),
        tijd(sprintf "revspace/sensors/knmi/%s/measured-at", $id);
}

if(index($_{msg}, '-v') != -1) {
    reply sprintf "%s", station("6215"), # Voorschoten
    reply sprintf "%s", station("6344"), # Rotterdam The Hague Airport
    reply sprintf "%s", station("6330"); # Hoek van Holland
} else {
    reply sprintf "%s", station("6215"); # Voorschoten
}
